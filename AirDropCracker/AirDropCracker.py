import yaml
from hashlib import sha256
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.progress import Progress
from rich import print
import threading
import time
import sqlite3
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkinter import scrolledtext

class MyException(Exception):
    def __init__(self,message):
        super().__init__(message)

class DBHelper:
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

class AirDropCracker:
    def __init__(self):
        self.config = self.get_config()
        self.stop_flag = False
        self.start_time = 0
        self.end_time = 0
        self.db = None
        self.values = []
        self.root = tk.Tk()
        self.root.title("AirDropCracker 作者：WXjzc")

        # 输入框
        self.head_label = tk.Label(self.root, text="哈希值前5位：")
        self.head_label.grid(row=0, column=0, padx=10, pady=10)
        self.head_entry = tk.Entry(self.root)
        self.head_entry.grid(row=0, column=1, padx=10, pady=10)

        self.tail_label = tk.Label(self.root, text="哈希值后5位：")
        self.tail_label.grid(row=1, column=0, padx=10, pady=10)
        self.tail_entry = tk.Entry(self.root)
        self.tail_entry.grid(row=1, column=1, padx=10, pady=10)

        # 按钮
        self.start_button = tk.Button(self.root, text="开始",
                                      command=lambda: self.thread_run(self.head_entry.get(), self.tail_entry.get()))
        self.start_button.grid(row=2, column=0, padx=10, pady=10)

        self.stop_button = tk.Button(self.root, text="停止", command=self.thread_stop)
        self.stop_button.grid(row=2, column=1, padx=10, pady=10)

        # 输出框
        self.output_text = scrolledtext.ScrolledText(self.root, width=50, height=10, background="darkgray")
        self.output_text.grid(row=3, column=0, columnspan=2, padx=10, pady=10)
        self.output_text.tag_configure('green', foreground='yellowgreen')
        self.output_text.tag_configure('yellow', foreground='yellow')
        self.output_text.tag_configure('red', foreground='red')
        self.output_text.tag_configure('blue', foreground='blue')


        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.center_window()
        self.root.mainloop()

    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    def get_from_db(self, head: str, tail: str) -> bool:
        self.db = DBHelper()
        ret = self.db.select(head, tail)
        self.db.close()
        if ret == []:
            print('[yellow]数据库中没有数据')
            self.output_text.insert(tk.END,'数据库中没有数据\n','yellow')
            return False
        for v in ret:
            phone = v[0]
            _hash = v[1]
            print(f'[green]手机号: {phone} | 哈希值: {_hash}')
            self.output_text.insert(tk.END, f'手机号: {phone} | 哈希值: {_hash}\n', 'green')
        return True

    def get_config(self) -> dict:
        try:
            with open('config.yml', encoding='utf8') as f:
                config = yaml.load(f, Loader=yaml.FullLoader)
        except Exception as e:
            messagebox.showerror('错误', 'config.yml文件不存在或格式错误')
        hlr = config['HLR']
        mac = config['MAC']
        cc = config['CC']
        length = config['length']
        if hlr is None:
            self.output_text.insert(tk.END, f'必须配置在config.yml中配置HLR列表，可以配置成[]\n', 'red')
            raise MyException('必须配置在config.yml中配置HLR列表，可以配置成[]')
        if mac is None or mac == []:
            self.output_text.insert(tk.END, f'必须配置在config.yml中配置MAC列表，且不能为空\n', 'red')
            raise MyException('必须配置在config.yml中配置MAC列表，且不能为空')
        if cc is None or cc == []:
            self.output_text.insert(tk.END, f'必须配置在config.yml中配置CC列表，且不能为空\n', 'red')
            raise MyException('必须配置在config.yml中配置CC列表，且不能为空')
        max_mac = max(mac)
        max_hlr = 0
        if hlr != []:
            max_hlr = max(hlr)
            pre_length = len(str(max_hlr))+len(str(max_mac))
        else:
            pre_length = len(str(max_mac))
        if length is None or length <= pre_length:
            self.output_text.insert(tk.END, f'必须配置在config.yml中配置length，且不能少于hlr和mac的长度之和\n', 'red')
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
            print(f'耗费时间：{round(self.end_time - self.start_time, 2)}秒')
            self.output_text.insert(tk.END, f'耗费时间：{round(self.end_time - self.start_time, 2)}秒\n', 'blue')
            print(f'[green]手机号: {phone} | 哈希值: {_hash}')
            self.output_text.insert(tk.END, f'手机号: {phone} | 哈希值: {_hash}\n', 'green')
            print(f'[yellow]破解仍在进行中...')
            self.output_text.insert(tk.END, f'破解仍在进行中...\n', 'yellow')
            return (int(phone), _hash, head, tail)
        if self.stop_flag:
            return 'wxjzc_stop'
        return ''

    def run(self, head: str, tail: str) -> None:
        pres = self.get_pre()
        len_mac = len(self.config['MAC'])
        length = self.config['true_length']
        if len(head) != 5 or len(tail) != 5:
            self.output_text.insert(tk.END, f'head和tail的长度必须为5\n', 'red')
            raise MyException('head和tail的长度必须为5')
        total_length = len(pres) * (10 ** length)
        self.start_time = time.time()
        for num in range(10 ** length):
            num = (length-len(str(num))) * '0' + str(num)
            for pre in pres:
                result = self.crack(pre + num, head, tail)
                if result == 'wxjzc_stop':
                    print("[red]破解终止")
                    self.output_text.insert(tk.END, '破解终止\n', 'red')
                    return
                if result != '':
                    self.db = DBHelper()
                    self.db.insert([result])
                    self.db.close()
            # 多线程反而会慢。。各种情况都试了一下，要么就是慢，要么是会卡死GUI和终端
            # with ThreadPoolExecutor(max_workers=len_mac) as executor:
            #     futures = [executor.submit(self.crack, pre+num, head, tail) for pre in pres]
            #     for future in futures:
            #         result = future.result()
            #         if result == 'wxjzc_stop':
            #             print("[red]破解终止")
            #             self.output_text.insert(tk.END, '破解终止\n', 'red')
            #             return
            #         if result != '':
            #             self.db = DBHelper()
            #             self.db.insert([result])
            #             self.db.close()

    def thread_run(self, head: str, tail: str):
        self.stop_flag = False
        t = threading.Thread(target=self.run, args=(head, tail))
        if not self.get_from_db(head, tail):
            print('[blue]开始破解')
            self.output_text.insert(tk.END, '开始破解\n', 'blue')
            t.start()

    def thread_stop(self):
        self.stop_flag = True

    def close(self):
        self.thread_stop()
        self.root.destroy()

if __name__ == '__main__':
    a = AirDropCracker()