package main

import (
	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/app"
)

var window fyne.Window

func main() {
	myApp := app.NewWithID("com.wxjzc.leveldbReader")
	window = myApp.NewWindow("leveldbReader")
	icon, _ := fyne.LoadResourceFromPath("icon.ico")
	window.SetIcon(icon)
	content := initUI()
	window.SetContent(content)
	window.Resize(fyne.NewSize(800, 600))
	window.SetFixedSize(true)
	window.CenterOnScreen()
	window.ShowAndRun()
}
