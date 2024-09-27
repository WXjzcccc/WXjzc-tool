import datetime
import pytz
import tkinter as tk
from tkinter import ttk


def timestamp_to_datetime(converted_time, origin_timezone='UTC', target_timezone='Asia/Shanghai'):
    _timezone = pytz.timezone(origin_timezone)
    converted_time = _timezone.localize(converted_time)
    converted_time = converted_time.astimezone(pytz.timezone(target_timezone))
    date_str = converted_time.strftime('%Y-%m-%d %H:%M:%S')
    return date_str


def ios_timestamp_to_datetime(timestamp, origin_timezone='UTC', target_timezone='Asia/Shanghai'):
    try:
        base_time = datetime.datetime(2001, 1, 1)
        delta = datetime.timedelta(seconds=timestamp)
        converted_time = base_time + delta
        return timestamp_to_datetime(converted_time, origin_timezone, target_timezone)
    except:
        return '解析失败'


def default_timestamp_to_datetime(timestamp, origin_timezone='UTC', target_timezone='Asia/Shanghai'):
    try:
        if len(str(timestamp)) == 13:
            dt = datetime.datetime.fromtimestamp(timestamp / 1000)
        else:
            dt = datetime.datetime.fromtimestamp(timestamp)
        return timestamp_to_datetime(dt, origin_timezone, target_timezone)
    except:
        return '解析失败'


def chrome_timestamp_to_datetime(timestamp, origin_timezone='UTC', target_timezone='Asia/Shanghai'):
    try:
        base_time = datetime.datetime(1601, 1, 1)
        delta = datetime.timedelta(microseconds=timestamp)
        converted_time = base_time + delta
        return timestamp_to_datetime(converted_time, origin_timezone, target_timezone)
    except:
        return '解析失败'


def nine_timestamp_to_datetime(timestamp, origin_timezone='UTC', target_timezone='Asia/Shanghai'):
    try:
        nine = int(format(timestamp, '.20f')[:9]) + 978307200
        dt = datetime.datetime.fromtimestamp(nine)
        return timestamp_to_datetime(dt, origin_timezone, target_timezone)
    except:
        return '解析失败'


class ToolTip(object):

    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def showtip(self, text):
        "Display text in tooltip window"
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 27
        y = y + cy + self.widget.winfo_rooty() + 27
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                      background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                      font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()


class GUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("时间戳转换器")

        # 设置列和行的权重
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_rowconfigure(3, weight=1)
        self.root.grid_rowconfigure(4, weight=1)
        self.root.grid_rowconfigure(5, weight=1)

        self.timestamp_label = ttk.Label(self.root, text="时间戳：")
        self.timestamp_label.grid(column=0, row=0, padx=10, pady=10, sticky="e")
        self.timestamp_entry = ttk.Entry(self.root, width=20)
        self.timestamp_entry.grid(column=1, row=0, padx=10, pady=10, sticky="w")

        # 创建时间戳类型下拉选择框
        self.timestamp_type_label = ttk.Label(self.root, text="时间戳类型：")
        self.timestamp_type_label.grid(column=0, row=1, padx=10, pady=10, sticky="e")
        self.methods = {
            "UNIX": default_timestamp_to_datetime,
            "Chrome/Webkit": chrome_timestamp_to_datetime,
            "iOS数据库中": ios_timestamp_to_datetime,
            "18位时间戳": nine_timestamp_to_datetime
        }
        self.timestamp_type_combobox = ttk.Combobox(self.root, values=list(self.methods.keys()), width=18)
        self.timestamp_type_combobox.current(0)
        self.timestamp_type_combobox.grid(column=1, row=1, padx=10, pady=10, sticky="w")

        # 创建时间戳的时区下拉选择框
        self.timestamp_tz_label = ttk.Label(self.root, text="时间戳的时区：")
        self.timestamp_tz_label.grid(column=0, row=2, padx=10, pady=10, sticky="e")
        self.timestamp_tz_combobox = ttk.Combobox(self.root, values=pytz.all_timezones, width=18)
        self.timestamp_tz_combobox.set('UTC')
        self.timestamp_tz_combobox.grid(column=1, row=2, padx=10, pady=10, sticky="w")

        # 创建目标时区下拉选择框
        self.target_tz_label = ttk.Label(self.root, text="目标时区：")
        self.target_tz_label.grid(column=0, row=3, padx=10, pady=10, sticky="e")
        self.target_tz_combobox = ttk.Combobox(self.root, values=pytz.all_timezones, width=18)
        self.target_tz_combobox.set('Asia/Shanghai')
        self.target_tz_combobox.grid(column=1, row=3, padx=10, pady=10, sticky="w")

        # 创建转换结果文本框
        self.result_label = ttk.Label(self.root, text="转换结果：")
        self.result_label.grid(column=0, row=4, padx=10, pady=10, sticky="e")
        self.result_text = tk.Entry(self.root, state="disabled", width=20)
        self.result_text.grid(column=1, row=4, padx=10, pady=10, sticky="w")
        self.result_text.bind("<Button-1>", self.copy_result)
        # 作者
        self.timestamp_label = ttk.Label(self.root, text="作者：WXjzc")
        self.timestamp_label.grid(column=0, row=5, padx=10, pady=10, sticky="e")
        # 创建转换按钮
        self.convert_button = ttk.Button(self.root, text="转换", command=self.do_transform)
        self.convert_button.grid(column=1, row=5, padx=10, pady=10, sticky="w")

        # 设置窗口居中
        self.center_window()

        self.root.mainloop()

    def copy_result(self, event):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.result_text.get())
        tooltip = ToolTip(self.result_text)
        tooltip.showtip("复制成功")
        self.root.after(1000, tooltip.hidetip)

    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    def do_transform(self):
        timestamp = self.timestamp_entry.get()
        method = self.timestamp_type_combobox.get()
        func = self.methods[method]
        origin_tz = self.timestamp_tz_combobox.get()
        target_tz = self.target_tz_combobox.get()
        try:
            date_str = func(int(timestamp), origin_tz, target_tz)
        except:
            date_str = func(float(timestamp), origin_tz, target_tz)
        self.result_text.config(state="normal")
        self.result_text.delete(0, tk.END)
        self.result_text.insert(tk.END, date_str)
        self.result_text.config(state="disabled")


if __name__ == "__main__":
    gui = GUI()