from PySide6.QtCore import QThread, Slot, Signal
from PySide6.QtWidgets import QWidget, QApplication, QPushButton, QLabel, QTextEdit, QLineEdit, QGridLayout
from PySide6.QtGui import QIcon
import yaml
from hashlib import sha256
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich import print
import time
import sqlite3
import os


class MyGUI(QWidget):
    def __init__(self):  # 重写构造方法
        super().__init__()
        self.setWindowTitle("AirDropCracker")
        self.setWindowIcon(QIcon("1.ico"))
        self.setup()  # 创建界面
        self.bind()  # 绑定函数

    def bind(self):
        self.button_start.clicked.connect(self.start_new_thread)  # 将按钮与开启新线程的槽函数通过click信号相连
        self.button_stop.clicked.connect(self.close_thread)  # 将按钮与停止线程的槽函数通过click信号相连
        self.button_clear.clicked.connect(lambda: self.text_edit.setText(""))  # 将按钮与清空文本的槽函数通过click信号相连

    def setup(self):
        layout = QGridLayout()  # 界面布局为垂直布局
        self.setLayout(layout)  # 设置layout布局
        self.resize(300, 400)  # 重新设置界面大小
        self.label_head = QLabel("请输入哈希值前5位:")  # 定义标签控件
        self.input_head = QLineEdit()
        self.label_tail = QLabel("请输入哈希值后5位:")  # 定义标签控件
        self.input_tail = QLineEdit()
        self.input_head.setMaxLength(5)
        self.input_tail.setMaxLength(5)
        self.button_start = QPushButton("开始")  # 定义按钮控件
        self.button_stop = QPushButton("停止")  # 定义按钮控件
        self.text_edit = QTextEdit()  # 定义可编辑文本框控件
        self.button_clear = QPushButton("清空输出")  # 定义按钮控件
        layout.addWidget(self.label_head, 0, 0)  # 放置标签控件
        layout.addWidget(self.input_head, 0, 1)  # 放置标签控件
        layout.addWidget(self.label_tail, 1, 0)  # 放置标签控件
        layout.addWidget(self.input_tail, 1, 1)  # 放置标签控件
        layout.addWidget(self.button_start, 2, 0, 1, 2)  # 放置按钮控件
        layout.addWidget(self.button_stop, 3, 0, 1, 2)  # 放置按钮控件
        layout.addWidget(self.text_edit, 4, 0, 1, 2)  # 放置文本框界面
        layout.addWidget(self.button_clear, 5, 0, 1, 2)  # 放置按钮控件

    def start_new_thread(self):
        print("启动新线程")
        head = self.input_head.text()
        tail = self.input_tail.text()
        self.thread1 = AirDropCracker(head, tail)  # 创建子线程thread1

        self.thread1.signal.connect(self.update_text)  # 【关键】将信号与槽函数连接
        self.thread1.start()  # 启动子线程thread1

    def close_thread(self):
        self.thread1.stop()

    @Slot(int)  # 定义一个槽函数, 在函数前放一个@Slot()表明其是一个槽函数
    def update_text(self, count):
        self.text_edit.append(f"{count}")  # 将计时器传来的信号展示在文本框中

    def closeEvent(self, event):
        self.close_thread()


class MyException(Exception):
    def __init__(self, message):
        super().__init__(message)


class DBHelper:
    signal = Signal(str)

    def __init__(self):
        self.conn = sqlite3.connect('airdrop.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS "airdrop" (
            	"phone"	INTEGER NOT NULL UNIQUE,
            	"hash"	TEXT,
            	"head"	TEXT,
            	"tail"	TEXT,
            	PRIMARY KEY("phone")
            )
        ''')
        self.conn.commit()

    def select(self, head: str, tail: str) -> list:
        self.cursor.execute(f"SELECT * FROM airdrop where head='{head}' and tail='{tail}'")
        return self.cursor.fetchall()

    def insert(self, values: list):
        try:
            self.cursor.executemany('INSERT INTO airdrop (phone, hash, head, tail) VALUES (?, ?, ?, ?)', values)
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            print(e)

    def close(self):
        self.conn.close()


class AirDropCracker(QThread):
    signal = Signal(str)

    def __init__(self, head, tail):
        super().__init__()
        self.config = None
        self.stop_flag = False
        self.start_time = 0
        self.end_time = 0
        self.db = DBHelper()
        self.values = []
        self.head = head
        self.tail = tail

    def get_from_db(self, head: str, tail: str) -> bool:
        self.db = DBHelper()
        ret = self.db.select(head, tail)
        self.db.close()
        if ret == []:
            print('[yellow]数据库中没有数据')
            self.color_emit('数据库中没有数据', 'brown')
            return False
        for v in ret:
            phone = v[0]
            _hash = v[1]
            print(f'[green]手机号: {phone} | 哈希值: {_hash}')
            self.color_emit(f'手机号: {phone} | 哈希值: {_hash}', 'green')
        return True

    def get_config(self) -> dict:
        if not os.path.exists('config.yml'):
            print('[yellow]未找到配置文件config.yml, 请先配置')
            self.color_emit('未找到配置文件config.yml, 请先配置', 'brown')
        with open('config.yml', encoding='utf8') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        try:
            hlr = config['HLR']
            mac = config['MAC']
            cc = config['CC']
            length = config['length']
            if hlr is None:
                self.color_emit('必须配置在config.yml中配置HLR列表，可以配置成[]', 'red')
                raise MyException('必须配置在config.yml中配置HLR列表，可以配置成[]')
            if mac is None or mac == []:
                self.color_emit('必须配置在config.yml中配置MAC列表，且不能为空', 'red')
                raise MyException('必须配置在config.yml中配置MAC列表，且不能为空')
            if cc is None or cc == []:
                self.color_emit('必须配置在config.yml中配置CC列表，且不能为空', 'red')
                raise MyException('必须配置在config.yml中配置CC列表，且不能为空')
        except Exception as e:
            self.color_emit(e, 'red')
            raise MyException(e)
        max_mac = max(mac)
        max_hlr = 0
        if hlr != []:
            max_hlr = max(hlr)
            pre_length = len(str(max_hlr)) + len(str(max_mac))
        else:
            pre_length = len(str(max_mac))
        if length is None or length <= pre_length:
            self.color_emit('必须配置在config.yml中配置length，且不能少于hlr和mac的长度之和', 'red')
            raise MyException('必须配置在config.yml中配置length，且不能少于hlr和mac的长度之和')
        else:
            config['true_length'] = length - pre_length
        return config

    @staticmethod
    def get_hash(phone: str) -> str:
        _sha = sha256()
        _sha.update(phone.encode('utf-8'))
        return _sha.hexdigest()

    def get_pre(self) -> list:
        ccs = self.config['CC']
        macs = self.config['MAC']
        hlrs = self.config['HLR']
        pres = []
        for cc in ccs:
            for mac in macs:
                if hlrs != []:
                    for hlr in hlrs:
                        pres.append(f'{cc}{mac}{hlr}')
                else:
                    pres.append(f'{cc}{mac}')
        return pres

    def crack(self, phone: str, head: str, tail: str):
        _hash = self.get_hash(phone)
        if _hash[:5] == head and _hash[-5:] == tail:
            self.end_time = time.time()
            self.color_emit(f'耗费时间：{round(self.end_time - self.start_time, 2)}秒', 'blue')
            print(f'耗费时间：{round(self.end_time - self.start_time, 2)}秒')
            self.color_emit(f'手机号: {phone} | 哈希值: {_hash}', 'green')
            print(f'[green]手机号: {phone} | 哈希值: {_hash}')
            print(f'[yellow]破解仍在进行中...')
            self.color_emit(f'破解仍在进行中...', 'brown')
            return (int(phone), _hash, head, tail)
        if self.stop_flag:
            return 'wxjzc_stop'
        return ''

    def _run(self, pre: str, head: str, tail: str) -> None:
        pres = self.get_pre()
        len_mac = len(self.config['MAC'])
        length = self.config['true_length']
        if len(head) != 5 or len(tail) != 5:
            self.color_emit('head和tail的长度必须为5', 'red')
            raise MyException('head和tail的长度必须为5')
        for num in range(10 ** length):
            num = (length - len(str(num))) * '0' + str(num)
            result = self.crack(pre + num, head, tail)
            if result == 'wxjzc_stop':
                self.color_emit('破解终止', 'red')
                print("[red]破解终止")
                return '破解终止'
            if result != '':
                self.db = DBHelper()
                self.db.insert([result])
                self.db.close()
        return '暴力破解结束'

    def color_emit(self, text, color):
        self.signal.emit(f'<span  style="color:{color};">{text}</span>')

    def thread_run(self, head: str, tail: str):
        self.config = self.get_config()
        self.stop_flag = False
        pres = self.get_pre()
        self.start_time = time.time()
        if not self.get_from_db(head, tail):
            print('[blue]开始破解')
            self.color_emit('开始破解', 'blue')
            rets = []
            with ThreadPoolExecutor(max_workers=len(pres)) as executor:
                futures = []
                for pre in pres:
                    futures.append(executor.submit(self._run, pre, head, tail))
                for future in as_completed(futures):
                    result = future.result()
                    rets.append(result)
                if ['暴力破解结束']*len(rets) == rets:
                    self.color_emit('暴力破解结束', 'green')
                    print("[green]暴力破解结束")
                    self.stop_flag = True
                    return

    def thread_stop(self):
        self.stop_flag = True

    def stop(self):
        self.thread_stop()

    def run(self):
        self.thread_run(self.head, self.tail)


# 运行应用界面程序
if __name__ == '__main__':
    app = QApplication([])  # 定义一个应用
    window = MyGUI()  # 定义一个界面
    window.show()  # 展示界面
    app.exec()  # 启动应用