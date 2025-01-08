package main

import (
	"fmt"
	"github.com/syndtr/goleveldb/leveldb"
	"strings"
)

type Reader struct {
	key   string
	value string
}

func formatBytes(data []byte) string {
	var builder strings.Builder
	builder.WriteString("b'")
	for _, b := range data {
		if b >= 32 && b <= 126 { // 可打印的 ASCII 字符
			builder.WriteByte(b)
		} else {
			builder.WriteString(fmt.Sprintf("\\x%02x", b)) // 不可打印字符转为 \x 形式
		}
	}
	builder.WriteString("'")
	return builder.String()
}

func readDb(dbPath string) []Reader {
	db, err := leveldb.OpenFile(dbPath, nil)
	if err != nil {
		showDialog("错误", "数据库打开失败！\n"+err.Error())
		return nil
	}
	iter := db.NewIterator(nil, nil)
	var readerList []Reader
	for iter.Next() {
		// Remember that the contents of the returned slice should not be modified, and
		// only valid until the next call to Next.
		key := iter.Key()
		value := iter.Value()
		reader := Reader{}
		reader.key = formatBytes(key)
		reader.value = formatBytes(value)
		readerList = append(readerList, reader)
	}
	iter.Release()
	err = iter.Error()
	defer db.Close()
	return readerList
}
