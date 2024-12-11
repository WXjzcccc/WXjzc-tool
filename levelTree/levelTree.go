package main

import (
	"bufio"
	"encoding/csv"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"
)

const (
	Reset  = "\x1b[0m"
	Red    = "\x1b[31m"
	Green  = "\x1b[32m"
	Yellow = "\x1b[33m"
	Blue   = "\x1b[34m"
)

func readData(file string) map[string]string {
	dic := make(map[string]string)
	fr, err := os.Open(file)
	if err != nil {
		panic(err)
	}
	defer func(fr *os.File) {
		err := fr.Close()
		if err != nil {
			panic(err)
		}
	}(fr)

	scanner := bufio.NewScanner(fr)
	for scanner.Scan() {
		line := scanner.Text()
		data := strings.Split(line, "\t")
		if len(data) == 1 {
			data = append(data, "") // 如果只有一个元素，手动添加空字符串
		}
		dic[data[0]] = data[1]
	}

	if err := scanner.Err(); err != nil {
		panic(err)
	}

	return dic
}

func getParents(uid string, levelData map[string]string, lst []string) []string {
	if levelData[uid] == "" {
		return lst
	}
	lst = append(lst, levelData[uid])
	return getParents(levelData[uid], levelData, lst)
}

func calculateSubordinateInfo(userTree map[string][]string, userId string) (int, int) {
	if _, ok := userTree[userId]; !ok {
		return 0, 0
	}

	maxDepth := 0
	totalSubordinates := 0

	for _, subId := range userTree[userId] {
		subCount, subDepth := calculateSubordinateInfo(userTree, subId)
		totalSubordinates += subCount + 1
		if subDepth+1 > maxDepth {
			maxDepth = subDepth + 1
		}
	}

	return totalSubordinates, maxDepth
}

func buildTree(levelData map[string]string) map[string][]string {
	tree := make(map[string][]string)
	for key, value := range levelData {
		userId := key
		superiorId := value
		if _, ok := tree[superiorId]; !ok {
			tree[superiorId] = []string{}
		}
		tree[superiorId] = append(tree[superiorId], userId)
	}
	return tree
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
	fmt.Printf("%s[+]请拖入文件，只包含id和上级id，以制表符分割，无需表头：\n", Yellow)

	var file string
	fmt.Scanln(&file)
	startTime := time.Now()

	file = strings.ReplaceAll(file, `"`, "")
	levelData := readData(file)
	total := []string{}
	user := make(map[string]map[string]interface{})
	tree := buildTree(levelData)

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
			"上级ID":   levelData[v],
			"所处层级": depth,
			"推荐链条": recommendChain,
			"下线数量": 0,
			"下线层数": 0,
		}
	}

	for v := range levelData {
		subCount, subDepth := calculateSubordinateInfo(tree, v)
		user[v]["下线数量"] = subCount
		user[v]["下线层数"] = subDepth
	}

	outputFile := filepath.Join(filepath.Dir(file), "tree.csv")
	fw, err := os.Create(outputFile)
	if err != nil {
		panic(err)
	}
	defer fw.Close()

	writer := csv.NewWriter(fw)
	defer writer.Flush()

	writer.Write([]string{"ID", "上级ID", "所处层级", "下线层数", "下线数量", "推荐链条"})
	for key, val := range user {
		writer.Write([]string{
			key,
			val["上级ID"].(string),
			fmt.Sprint(val["所处层级"]),
			fmt.Sprint(val["下线层数"]),
			fmt.Sprint(val["下线数量"]),
			val["推荐链条"].(string),
		})
	}
	writer.Flush()
	fw.Close()
	fmt.Printf("%s[√]处理完成，耗时%.2f秒\n", Green, time.Since(startTime).Seconds())
	fmt.Println("按任意键退出程序")
	fmt.Scanln()
}
