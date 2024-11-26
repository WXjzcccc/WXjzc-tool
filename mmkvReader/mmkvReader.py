import binascii
from tabnanny import check

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPainter, QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QLineEdit, QPushButton, QTabWidget, QTableWidget, QTableWidgetItem, QTextEdit, QMessageBox, QRadioButton,
    QGridLayout, QButtonGroup, QFileDialog
)
from qt_material import apply_stylesheet
import mmkv
import os


def show_message(title :str, text: str, icon = QMessageBox.Icon.Warning):
    message_box = QMessageBox()
    message_box.setWindowTitle(title)
    message_box.setText(text)
    message_box.setIcon(icon)
    message_box.exec()


class mmkvReader:

    def __init__(self, path: str):
        if os.path.exists(path):
            if os.path.isdir(path):
                if self.check_path(path):
                    mmkv.MMKV.initializeMMKV(path)
                self.path = path
                self.file = False
                self.fileName = ''
            else:
                if self.check_path(os.path.dirname(path)):
                    mmkv.MMKV.initializeMMKV(os.path.dirname(path))
                self.path = os.path.dirname(path)
                self.file = True
                self.fileName = os.path.basename(path)
        else:
            show_message('错误！','输入的路径不正确！')


    def check_path(self,path):
        files = os.listdir(path)
        flag = False
        for file in files:
            if file.endswith('.crc'):
                flag = True
                break
        if not flag:
            show_message('错误！', '未找到crc文件，请重新选择路径！')
        return flag

    def listObjects(self) -> list:
        '''获取目录下的文件'''
        lst = []
        if not self.file:
            files = os.listdir(self.path)
            for file in files:
                if not file.endswith('.crc'):
                    lst.append(file)
        return lst

    def getObject(self, name: str, cryptKey: str = ''):
        '''指定存储数据的文件，返回可读取的对象'''
        if cryptKey != '':
            # 处理加密的内容
            kv = mmkv.MMKV(name, cryptKey=cryptKey)
        else:
            kv = mmkv.MMKV(name)
        return kv

    def getAllTypeValue(self, kv, key: str):
        '''由于无法进行类型判断，因此获取每个键的所有类型的值'''
        dic = {
            'bool': kv.getBool(key),
            'int32': kv.getInt(key),
            'uint32': kv.getUInt(key),
            'int64': kv.getLongInt(key),
            'uint64': kv.getLongUInt(key),
            'float': kv.getFloat(key),
            'bytes': binascii.hexlify(kv.getBytes(key)).decode()
        }
        try:
            dic.update({'string': kv.getString(key)})
        except:
            pass
        return dic

    def getObjectAllValue(self, kv):
        '''获取所有值'''
        keys = kv.keys()
        dic = {}
        for key in keys:
            dic[key] = self.getAllTypeValue(kv, key)
        return dic

    def getDirAllValue(self):
        '''获取mmkv目录下所有文件的所有键值，但是不支持加密，因为不同文件可以使用不同的密钥'''
        if not self.file:
            dic = {}
            files = os.listdir(self.path)
            errs = []
            for file in files:
                if not file.endswith('.crc'):
                    try:
                        kv = self.getObject(file)
                        dic[file] = self.getObjectAllValue(kv)
                    except:
                        errs.append(file)
            if errs:
                show_message('错误！', f'{errs}读取异常!')
        else:
            kv = self.getObject(self.fileName)
            return self.getObjectAllValue(kv)
        return dic

class MainWindow(QMainWindow):

    def __init__(self):
        # 主布局
        super().__init__()
        self.setWindowTitle("mmkvReader")
        self.setWindowIcon(QIcon("icon.ico"))
        self.dir_path = ''
        self.file_path = ''
        main_layout = QVBoxLayout()

        # 上部区域布局
        top_layout = QHBoxLayout()
        self.init_top_layout(top_layout)

        # 下部区域布局
        bottom_layout = QVBoxLayout()
        self.tab_widget = QTabWidget()
        bottom_layout.addWidget(self.tab_widget)

        # 主布局合并
        main_layout.addLayout(top_layout, 1)
        main_layout.addLayout(bottom_layout, 2)

        # 设置主窗口布局
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def init_top_layout(self, layout):
        # 左侧部分
        left_widget = QWidget()
        left_layout = QGridLayout()

        # 文件选择器
        self.file_radio = QRadioButton("文件选择器")
        self.file_radio.setChecked(True)
        self.file_button = QPushButton("选择文件")
        self.file_button.clicked.connect(self.choose_file)

        # 目录选择器
        self.dir_radio = QRadioButton("目录选择器")
        self.dir_button = QPushButton("选择目录")
        self.dir_button.clicked.connect(self.choose_directory)
        self.dir_button.setEnabled(False)

        # 单选按钮组，确保只能选择文件或目录
        self.radio_group = QButtonGroup()
        self.radio_group.addButton(self.file_radio)
        self.radio_group.addButton(self.dir_radio)
        self.file_radio.toggled.connect(self.toggle_selector)

        # 密码输入框
        password_label = QLabel("密码:")
        self.password_input = QLineEdit()

        # 确定按钮
        confirm_button = QPushButton("确定")
        confirm_button.clicked.connect(self.confirm_action)

        # 布局设置
        left_layout.addWidget(self.file_radio, 0, 0)
        left_layout.addWidget(self.file_button, 0, 1)
        left_layout.addWidget(self.dir_radio, 1, 0)
        left_layout.addWidget(self.dir_button, 1, 1)
        left_layout.addWidget(password_label, 2, 0)
        left_layout.addWidget(self.password_input, 2, 1)
        left_layout.addWidget(confirm_button, 3, 0, 1, 2)

        left_widget.setLayout(left_layout)

        # 右侧部分
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        self.description_text.setFontFamily("Consolas")
        self.description_text.setFontPointSize(8)
        self.description_text.setText("""
                     _           ____                _           
 _ __ ___  _ __ ___ | | ____   _|  _ \ ___  __ _  __| | ___ _ __ 
| '_ ` _ \| '_ ` _ \| |/ /\ \ / / |_) / _ \/ _` |/ _` |/ _ \ '__|
| | | | | | | | | | |   <  \ V /|  _ <  __/ (_| | (_| |  __/ |   
|_| |_| |_|_| |_| |_|_|\_\  \_/ |_| \_\___|\__,_|\__,_|\___|_|   

Author: WXjzc
1.选择目录时不支持密码，输出目录下所有mmkv的键值
2.选择文件时支持密码，输出该文件的键值
3.请确保mmkv的crc文件存在，如果选错目录，可能会对你的文本文件造成影响
""")

        right_layout.addWidget(self.description_text)
        right_widget.setLayout(right_layout)

        # 合并左右部分
        layout.addWidget(left_widget, 1)
        layout.addWidget(right_widget, 2)

    def show_table(self, panel_data: dict):
        for key, value in panel_data.items():
            self.add_tab(key,value)

    def init_bottom_layout(self,data,name=''):
        # Tab Widget
        if not name:
            for key,value in data.items():
                tab = QWidget()
                tab_layout = QVBoxLayout()
                rows = len(value.keys())
                table = QTableWidget(rows, 8)
                cols = ['bool','int32','uint32','int64','uint64','float','bytes','string']
                table.setHorizontalHeaderLabels(cols)
                table.setVerticalHeaderLabels(value.keys())
                for index_r,row in enumerate(value.keys()):
                    for index_c,col in enumerate(cols):
                        try:
                            table.setItem(index_r, index_c, QTableWidgetItem(str(value[row][col])))
                        except:
                            table.setItem(index_r, index_c, QTableWidgetItem(''))
                tab_layout.addWidget(table)
                table.horizontalHeader().setStretchLastSection(True)
                table.horizontalHeader().setDefaultSectionSize(120)
                table.setMinimumWidth(600)
                tab.setLayout(tab_layout)
                self.tab_widget.addTab(tab, key)
        else:
            tab = QWidget()
            tab_layout = QVBoxLayout()
            rows = len(data.keys())
            table = QTableWidget(rows, 8)
            cols = ['bool','int32','uint32','int64','uint64','float','bytes','string']
            table.setHorizontalHeaderLabels(cols)
            table.setVerticalHeaderLabels(data.keys())
            for index_r,row in enumerate(data.keys()):
                for index_c,col in enumerate(cols):
                    try:
                        table.setItem(index_r, index_c, QTableWidgetItem(str(data[row][col])))
                    except:
                        table.setItem(index_r, index_c, QTableWidgetItem(''))
            tab_layout.addWidget(table)
            table.horizontalHeader().setStretchLastSection(True)
            table.horizontalHeader().setDefaultSectionSize(120)
            table.setMinimumWidth(600)
            tab.setLayout(tab_layout)
            self.tab_widget.addTab(tab, name)


    def choose_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文件")
        if file_path:
            self.description_text.append(f"选中文件: {file_path}")
            self.file_path = file_path

    def choose_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择目录")
        if dir_path:
            self.description_text.append(f"选中目录: {dir_path}")
            self.dir_path = dir_path

    def toggle_selector(self):
        if self.file_radio.isChecked():
            self.file_button.setEnabled(True)
            self.dir_button.setEnabled(False)
        else:
            self.file_button.setEnabled(False)
            self.dir_button.setEnabled(True)

    def confirm_action(self):
        self.tab_widget.clear()
        password = self.password_input.text()
        if self.file_radio.isChecked():
            reader = mmkvReader(self.file_path)
            kv = reader.getObject(os.path.basename(self.file_path),password)
            data = reader.getObjectAllValue(kv)
            self.init_bottom_layout(data,os.path.basename(self.file_path))
        elif self.dir_radio.isChecked():
            reader = mmkvReader(self.dir_path)
            kvs = reader.getDirAllValue()
            self.init_bottom_layout(kvs)


if __name__ == "__main__":
    app = QApplication([])
    apply_stylesheet(app, theme='dark_amber.xml')
    window = MainWindow()
    window.resize(800, 600)
    window.show()
    app.exec()