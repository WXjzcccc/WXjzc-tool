import pymysql
import pandas as pd
from rich import print,pretty
from rich.progress import track
import sys
import os
import warnings
import csv

# 美化输出
def my_input(str):
    print(str,end='')
    return input()

class DB:
    connection = None
    sql = None
    def __init__(self,host='localhost',port=3306,user='root',pwd='root',database='',charset='utf8'):
        try:
            self.connection = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=pwd,
                database=database,
                charset=charset
            )
            print('[bold green][√]\t连接成功')
        except Exception as e:
            print(f'[bold red][-]\t数据库连接异常：{e}')
            sys.exit()

    def get_sql(self,file):
        try:
            with open(file,'r',encoding='utf8') as fr:
                self.sql = fr.read()
        except Exception as e:
            print(f'[bold red][-]\tSQL读取异常：{e}')

    def deal_sql(self,nums):
        sqls = []
        ori_sql = self.sql.replace(';','')
        # 一般分割不超过100个文件
        for i in range(100):
            tmp_sql = ori_sql + f' limit {i*nums+1},{nums}'
            sqls.append(tmp_sql)
        return sqls

    def to_file(self,df:pd.DataFrame,file,type):
        try:
            if type == 'xlsx':
                df.to_excel(file,index=False)
            elif type == 'csv':
                df.to_csv(file,index=False)
            else:
                print('[bold red][×]\t未知类型')
        except Exception as e:
            print(f'[bold red][-]\t保存文件{file}失败：{e}')

    def do_select(self,nums,file,type):
        sqls = self.deal_sql(nums)
        if type == '1':
            type = 'xlsx'
        elif type == '2':
            type = 'csv'
        else:
            print('[bold red][×]\t未知类型')
            return
        idx = 0
        for sql in track(sqls,description='处理中'):
            df = pd.read_sql(sql=sql,con=self.connection)
            idx += 1
            if df.empty:
                break
            else:
                self.to_file(df,file.replace('.',f'-{idx*nums}.'),type)

    def do_select_sscursor(self,nums,file):
        sqls = self.deal_sql(nums)
        idx = 0
        cursor = self.connection.cursor(pymysql.cursors.SSCursor)
        for sql in track(sqls,description='处理中'):
            cursor.execute(sql)
            idx += 1
            _len = 2
            columns = [desc[0] for desc in cursor.description]
            with open(file.replace('.',f'-{idx*nums}.'),'w',newline='',encoding='utf8') as fw:
                writer = csv.writer(fw)
                writer.writerow(columns)
                for row in cursor:
                    _len += 1
                    writer.writerow(row)
            if _len == 2:
                os.remove(file.replace('.',f'-{idx*nums}.'))
                break

    def close(self):
        self.connection.close()


if __name__ == '__main__':
    warnings.simplefilter('ignore',category=UserWarning)
    pretty.install()
    print('[bold green]MySQL数据导出，将大表分割导出若干csv或者xlsx文件，注意分割文件数量不能超过100')
    host = my_input('[bold yellow][+]\t请输入host（默认localhost）：')
    port = my_input('[bold yellow][+]\t请输入端口（默认3306）：')
    user = my_input('[bold yellow][+]\t请输入用户（默认root）：')
    pwd = my_input('[bold yellow][+]\t请输入密码（默认root）：')
    database = ''
    while True:
        database = my_input('[bold yellow][+]\t请输入数据库：')
        if not database:
            continue
        else:
            break
    charset = my_input('[bold yellow][+]\t请输入编码（默认utf8）：')
    if not host:
        host = '127.0.0.1'
    if not port:
        port = 3306
    else:
        port = int(port)
    if not user:
        user = 'root'
    if not pwd:
        pwd = 'root'
    if not charset:
        charset = 'utf8'
    db = DB(host,port,user,pwd,database,charset)
    sql_file = my_input('[bold yellow][+]\t请输入SQL文件路径，注意不要使用limit：')
    db.get_sql(sql_file)
    nums = my_input('[bold yellow][+]\t请输入分片长度：')
    cur = my_input('[bold yellow][+]\t是否采用流式传输（此方式内存占用极低，只支持生成csv，1确认）：')
    if cur == '1':
        file = my_input('[bold yellow][+]\t请输入导出文件路径：')
        db.do_select_sscursor(int(nums),file)
    else:
        _type = my_input('[bold yellow][+]\t请输入导出文件类型（1为xlsx，2为csv）：')
        file = my_input('[bold yellow][+]\t请输入导出文件路径：')
        db.do_select(int(nums),file,_type)
    db.close()
    my_input('[bold green]\t处理完成，按任意键退出！')