package main

import (
	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/container"
	"fyne.io/fyne/v2/dialog"
	"fyne.io/fyne/v2/widget"
	"log"
	"strconv"
	"strings"
)

type myTable struct {
	heads  []string
	reader []Reader
	/*
				heads应该是像这样的形式
		        ["姓名","密码"]
				data应该是像这样的形式
				[
					["张三","123456"],
		            ["李四","654321"],
				]
	*/
}

func initUI() fyne.CanvasObject {
	con := container.NewBorder(nil, nil, nil, nil, nil)
	fileEntry := widget.NewEntry()
	fileEntry.SetPlaceHolder("请输入levelDB目录")
	folderButton := widget.NewButton("选择文件夹", func() {
		dialog.ShowFolderOpen(func(f fyne.ListableURI, err error) {
			log.Println(err, f)
			if err == nil {
				if f != nil {
					temp := strings.Replace(f.String(), "file://", "", -1)
					ret := strings.Replace(temp, `"`, "", -1)
					fileEntry.SetText(ret)
				}
			} else {
				log.Println(err)
			}
		}, window)
	})
	vbox := container.NewMax()
	runButton := widget.NewButton("读取", func() {
		path := fileEntry.Text
		mt := myTable{[]string{"键", "值"}, readDb(path)}
		vbox.RemoveAll()
		vbox.Add(mt.buildTable())
	})
	buttonL := widget.NewFormItem("文件", container.NewVBox(fileEntry, folderButton, runButton))
	form := widget.NewForm(buttonL)

	_split := container.NewVSplit(form, vbox)
	_split.SetOffset(0.1)
	con.Add(_split)
	return con
}

func splitText(text string, size int) string {
	ret := ""
	for idx, ch := range text {
		ret += string(ch)
		if (idx+1)%size == 0 {
			ret += "\n"
		}
	}
	return ret
}

func (t *myTable) buildTable() *widget.Table {
	table := widget.NewTable(
		func() (int, int) {
			if t.reader == nil {
				return 0, 2
			}
			rows := len(t.reader)
			cols := len(t.heads)
			return rows, cols
		},
		func() fyne.CanvasObject {
			return widget.NewLabel("template")
		},
		func(id widget.TableCellID, o fyne.CanvasObject) {
			maxSize := 45
			if id.Col == 0 {
				if len(t.reader[id.Row].key) > maxSize {
					o.(*widget.Label).SetText(t.reader[id.Row].key[:maxSize] + "...")
				} else {
					o.(*widget.Label).SetText(t.reader[id.Row].key)
				}
			} else {
				if len(t.reader[id.Row].value) > maxSize {
					o.(*widget.Label).SetText(t.reader[id.Row].value[:maxSize] + "...")
				} else {
					o.(*widget.Label).SetText(t.reader[id.Row].value)
				}
			}
		})
	table.ShowHeaderRow = true
	table.ShowHeaderColumn = true
	table.CreateHeader = func() fyne.CanvasObject {
		return widget.NewLabel("template")
	}
	table.UpdateHeader = func(id widget.TableCellID, o fyne.CanvasObject) {
		b := o.(*widget.Label)
		if id.Col == -1 {
			b.SetText(strconv.Itoa(id.Row))
		} else {
			b.SetText(t.heads[id.Col])
		}
	}
	table.SetColumnWidth(0, 350)
	table.SetColumnWidth(1, 350)

	table.OnSelected = func(id widget.TableCellID) {
		fullText := ""
		if id.Col == 0 {
			fullText = t.reader[id.Row].key
		} else {
			fullText = t.reader[id.Row].value
		}
		tg := widget.NewTextGridFromString(splitText(fullText, 50))
		sh := container.NewVScroll(tg)
		sh.SetMinSize(fyne.NewSize(400, 200))
		window.Clipboard().SetContent(fullText)
		// 弹出对话框显示完整内容
		dialog.ShowCustom(
			"完整内容",
			"关闭（内容已自动复制到剪贴板）",
			sh, // 支持滚动h
			window,
		)

	}
	return table
}

func showDialog(title, message string) {
	dialog.NewInformation(title, message, window).Show()
}
