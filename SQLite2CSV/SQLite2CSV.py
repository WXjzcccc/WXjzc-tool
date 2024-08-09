import sqlite3
import pandas as pd
import os
import sys
from rich import print
from rich.progress import Progress
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_connection(db_file) -> sqlite3.Connection:
    conn = sqlite3.connect(db_file)
    return conn

def get_tables(cursor :sqlite3.Cursor) -> list:
    '''
    @cursor:    数据库cursor

    获取数据库中的所有表名
    '''
    sql = "SELECT name FROM sqlite_master WHERE type='table';"
    cursor.execute(sql)
    res = cursor.fetchall()
    table_list = [v[0] for v in res]
    return table_list

def table2csv(table:str,conn:sqlite3.Connection,db_name:str,out_path:str):
    '''
    @table:     待转换的表名
    @conn:      数据库连接
    @db_name:   数据库名称
    @out_path:  导出路径

    将表转为csv
    '''
    if not os.path.exists(out_path):
        os.makedirs(out_path)
    db_out_path = os.path.join(out_path,db_name)
    if not os.path.exists(db_out_path):
        os.makedirs(db_out_path)
    df = pd.read_sql(f'select * from `{table}`',conn)
    file_path = os.path.join(db_out_path,f'{table}.csv')
    df.to_csv(file_path,index=False)

def do_transfer(db_file,out_path):
    connection = get_connection(db_file)
    cursor = connection.cursor()
    tables = get_tables(cursor)
    basename = os.path.basename(db_file)
    if tables == []:
        print(f'[red][✘]异常:<{basename}>中没有表')
    for table in tables:
        try:
            table2csv(table,connection,basename.replace('.','_'),out_path)
        except Exception as e:
            print(f'[red][✘]查询<{basename}>时出现异常：{e}')
    connection.close()

def detect_sqlite(db_file,db_files:list):
    if os.path.isfile(db_file):
        with open(db_file,'rb') as fr:
            head = fr.read(16)
            if head == b'SQLite format 3\x00':
                db_files.append(db_file)

print('''
  ____    ___   _      _  _         ____    ____  ____ __     __
 / ___|  / _ \ | |    (_)| |_  ___ |___ \  / ___|/ ___|\ \   / /
 \___ \ | | | || |    | || __|/ _ \  __) || |    \___ \ \ \ / / 
  ___) || |_| || |___ | || |_|  __/ / __/ | |___  ___) | \ V /  
 |____/  \__\_\|_____||_| \__|\___||_____| \____||____/   \_/   
                                                                Author: WXjzc
''')
print('[yellow][＋]请拖入需要批量处理的SQLite数据库的文件夹：',end='')
db_path = input()
if not os.path.exists(db_path) or not os.path.isdir(db_path):
    print('[red][✘]输入的路径不正确或不存在！')
    input()
    sys.exit(-1)
files = os.listdir(db_path)
db_files = []
with ThreadPoolExecutor(max_workers=8) as executor:
        # 提交任务
    futures = {executor.submit(detect_sqlite,os.path.join(db_path,file),db_files):file for file in files}
    for future in as_completed(futures):
        try:
            future.result()  # 获取结果
        except Exception as e:
            print(f"[red][✘]出现异常: {e}")

if db_files == []:
    print('[red][✘]输入的路径中不包含SQLite数据库')
    input()
    sys.exit(-1)
print(f'[green][✔]检测到<{len(db_files)}>个SQLite文件')
print('[yellow][＋]请拖入生成的csv的目标目录：',end='')
out_path = input()
if not os.path.exists(out_path):
    os.makedirs(out_path)
with Progress() as progress:
    # 用于加载进度条
    task = progress.add_task("[blue][※]正在处理", total=len(db_files))

    # 创建线程池，最大8个线程
    with ThreadPoolExecutor(max_workers=8) as executor:
        # 提交任务
        futures = {executor.submit(do_transfer,db_file,out_path):db_file for db_file in db_files}
        for future in as_completed(futures):
            try:
                future.result()  # 获取结果
                progress.update(task, advance=1) # 更新进度条
            except Exception as e:
                print(f"[red][✘]出现异常: {e}")
print('[green][✔]处理完成！按任意键退出')
input()