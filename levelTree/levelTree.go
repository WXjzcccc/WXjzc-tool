package main

import (
	"bufio"
	"encoding/csv"
	"fmt"
	"github.com/fvbommel/sortorder"
	"github.com/guanguans/id-validator"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"time"
)

const (
	Reset               = "\x1b[0m"
	Red                 = "\x1b[31m"
	Green               = "\x1b[32m"
	Yellow              = "\x1b[33m"
	Blue                = "\x1b[34m"
	quchongTotal        = "下线数量(身份证去重)"
	quchongTotalChecked = "下线数量(身份证去重且通过校验)"
	zhijieTotal         = "直接下线数量(身份证去重)"
	zhijieTotalChecked  = "直接下线数量(身份证去重且通过校验)"
)

type UserData struct {
	SuperiorID string
	IDCard     string
}

func readData(file string) (map[string]UserData, bool) {
	dic := make(map[string]UserData)
	hasIDCard := false

	fr, err := os.Open(file)
	if err != nil {
		panic(err)
	}
	defer fr.Close()

	scanner := bufio.NewScanner(fr)
	lineCount := 0
	for scanner.Scan() {
		line := scanner.Text()
		data := strings.Split(line, "\t")

		if lineCount == 0 {
			// 检查第一行是否有三列数据
			if len(data) >= 3 && data[2] != "" {
				hasIDCard = true
			}
		}

		if len(data) == 1 {
			data = append(data, "") // 如果只有一个元素，手动添加空字符串
		}

		userData := UserData{
			SuperiorID: data[1],
		}

		if hasIDCard && len(data) >= 3 {
			userData.IDCard = data[2]
		}

		dic[data[0]] = userData
		lineCount++
	}

	if err := scanner.Err(); err != nil {
		panic(err)
	}
	return dic, hasIDCard
}

func getParents(uid string, levelData map[string]UserData, lst []string) []string {
	if levelData[uid].SuperiorID == "" {
		return lst
	}
	lst = append(lst, levelData[uid].SuperiorID)
	return getParents(levelData[uid].SuperiorID, levelData, lst)
}

func calculateSubordinateInfo(userTree map[string][]string, idCardMap map[string]string, userId string, hasIDCard bool) (totalSubordinates, maxDepth, directSubordinates int, allUniqueSubordinates, allUniqueSubordinatesChecked, directUniqueSubordinates, directUniqueSubordinatesChecked map[string]bool) {
	allUniqueSubordinates = make(map[string]bool)
	allUniqueSubordinatesChecked = make(map[string]bool)
	directUniqueSubordinates = make(map[string]bool)
	directUniqueSubordinatesChecked = make(map[string]bool)

	if _, ok := userTree[userId]; !ok {
		return 0, 0, 0, allUniqueSubordinates, allUniqueSubordinatesChecked, directUniqueSubordinates, directUniqueSubordinatesChecked
	}

	directSubordinates = len(userTree[userId])
	maxDepth = 0
	for _, subId := range userTree[userId] {
		subCount, subDepth, _, subAllUnique, _, _, _ := calculateSubordinateInfo(userTree, idCardMap, subId, hasIDCard)
		totalSubordinates += subCount + 1
		if subDepth+1 > maxDepth {
			maxDepth = subDepth + 1
		}

		// 合并间接下线的唯一身份证
		if hasIDCard {
			for idCard := range subAllUnique {
				allUniqueSubordinates[idCard] = true
				if idvalidator.IsValid(idCard, false) {
					allUniqueSubordinatesChecked[idCard] = true
				}
			}
		}
	}

	// 添加直接下线的身份证
	if hasIDCard {
		for _, subId := range userTree[userId] {
			if idCard, ok := idCardMap[subId]; ok {
				directUniqueSubordinates[idCard] = true
				allUniqueSubordinates[idCard] = true
				if idvalidator.IsValid(idCard, false) {
					allUniqueSubordinatesChecked[idCard] = true
					directUniqueSubordinatesChecked[idCard] = true
				}
			}
		}
	}
	return totalSubordinates, maxDepth, directSubordinates,
		allUniqueSubordinates, allUniqueSubordinatesChecked, directUniqueSubordinates, directUniqueSubordinatesChecked
}

func buildTree(levelData map[string]UserData) map[string][]string {
	tree := make(map[string][]string)
	for key, value := range levelData {
		userId := key
		superiorId := value.SuperiorID
		if _, ok := tree[superiorId]; !ok {
			tree[superiorId] = []string{}
		}
		tree[superiorId] = append(tree[superiorId], userId)
	}
	return tree
}

func buildIDCardMap(levelData map[string]UserData) map[string]string {
	idCardMap := make(map[string]string)
	for userId, data := range levelData {
		idCardMap[userId] = data.IDCard
	}
	return idCardMap
}

func calculateAllUsers(user map[string]map[string]interface{}, tree map[string][]string, idCardMap map[string]string, hasIDCard bool) {
	var wg sync.WaitGroup
	mu := sync.Mutex{} // 保护 user map 的并发写入

	for v := range user {
		wg.Add(1)
		go func(userId string) {
			defer wg.Done()
			subCount, subDepth, directSubCount, allUnique, allUniqueChecked, directUnique, directUniqueChecked :=
				calculateSubordinateInfo(tree, idCardMap, userId, hasIDCard)

			mu.Lock()
			defer mu.Unlock()
			user[userId]["下线数量"] = subCount
			user[userId]["下线层数"] = subDepth
			user[userId]["直接下线数量"] = directSubCount
			if hasIDCard {
				currentIdCard := idCardMap[userId]
				delete(allUnique, currentIdCard)
				delete(directUnique, currentIdCard)
				delete(allUniqueChecked, currentIdCard)
				delete(directUniqueChecked, currentIdCard)
				user[userId][quchongTotal] = len(allUnique)
				user[userId][quchongTotalChecked] = len(allUniqueChecked)
				user[userId][zhijieTotal] = len(directUnique)
				user[userId][zhijieTotalChecked] = len(directUniqueChecked)
			}
		}(v)
	}
	wg.Wait()
}

func main() {
	fmt.Println(`
 _                _ _____
| | _____   _____| |_   _| __ ___  ___
| |/ _ \ \ / / _ \ | | || '__/ _ \/ _ \
| |  __/\ V /  __/ | | || | |  __/  __/
|_|\___| \_/ \___|_| |_||_|  \___|\___|
                                       Author: WXjzc
`)
	fmt.Printf("%s[!]请确保只有顶层用户的上级ID为空值，其他用户必须要有上级\n", Blue)
	fmt.Printf("%s[+]请拖入文件，包含id和上级id(2列)，或id、上级id和身份证号(3列)，无须表头，以制表符分割：\n", Yellow)

	var file string
	fmt.Scanln(&file)
	startTime := time.Now()

	file = strings.ReplaceAll(file, `"`, "")
	levelData, hasIDCard := readData(file)
	total := []string{}
	user := make(map[string]map[string]interface{})
	tree := buildTree(levelData)
	idCardMap := buildIDCardMap(levelData)

	for v := range levelData {
		lst := getParents(v, levelData, []string{v})
		for i := 0; i < len(lst)/2; i++ {
			lst[i], lst[len(lst)-i-1] = lst[len(lst)-i-1], lst[i]
		}
		depth := len(lst)
		tmp := make([]string, len(lst))
		for i, item := range lst {
			tmp[i] = item
		}
		recommendChain := strings.Join(tmp, "->")
		total = append(total, recommendChain)

		user[v] = map[string]interface{}{
			"上级ID":              levelData[v].SuperiorID,
			"所处层级":              depth,
			"推荐链条":              recommendChain,
			"下线数量":              0,
			"下线层数":              0,
			"直接下线数量":            0,
			quchongTotal:        0,
			quchongTotalChecked: 0,
			zhijieTotal:         0,
			zhijieTotalChecked:  0,
		}
	}
	calculateAllUsers(user, tree, idCardMap, hasIDCard) // 多线程并行计算
	outputFile := filepath.Join(filepath.Dir(file), "tree.csv")
	fw, err := os.Create(outputFile)
	if err != nil {
		panic(err)
	}
	defer fw.Close()

	writer := csv.NewWriter(fw)
	defer writer.Flush()

	keys := make([]string, 0, len(user))
	for k := range user {
		keys = append(keys, k)
	}
	sort.Slice(keys, func(i, j int) bool {
		return sortorder.NaturalLess(keys[i], keys[j])
	})

	headers := []string{"ID", "上级ID", "所处层级", "下线层数", "下线数量", "直接下线数量"}
	if hasIDCard {
		headers = append(headers, quchongTotal, quchongTotalChecked, zhijieTotal, zhijieTotalChecked)
	}
	headers = append(headers, "推荐链条")
	writer.Write(headers)

	for _, key := range keys {
		record := []string{
			key,
			user[key]["上级ID"].(string),
			fmt.Sprint(user[key]["所处层级"]),
			fmt.Sprint(user[key]["下线层数"]),
			fmt.Sprint(user[key]["下线数量"]),
			fmt.Sprint(user[key]["直接下线数量"]),
		}
		if hasIDCard {
			record = append(record,
				fmt.Sprint(user[key][quchongTotal]),
				fmt.Sprint(user[key][quchongTotalChecked]),
				fmt.Sprint(user[key][zhijieTotal]),
				fmt.Sprint(user[key][zhijieTotalChecked]),
			)
		}
		record = append(record, user[key]["推荐链条"].(string))
		writer.Write(record)
	}

	writer.Flush()
	fw.Close()
	fmt.Printf("%s[√]处理完成，耗时%.2f秒\n", Green, time.Since(startTime).Seconds())
	fmt.Println("按任意键退出程序")
	fmt.Scanln()
}
