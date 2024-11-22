import pdfplumber
import pandas as pd
import os
from rich import print
import sys

def read_pdf_tables(pdf_path :str) -> list:
    '''

    :param pdf_path: pdf表格路径
    :return: 表格内容
    '''
    with pdfplumber.open(pdf_path) as pdf:
        table_data = []

        # 逐页读取PDF中的表格数据
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                table_data.append(table)
    return table_data

def get_dataframe(table_data :list) -> pd.DataFrame:
    '''

    :param table_data: 读取好的表格数据
    :return: 转换后的dataframe
    '''
    df_data = []
    for table in table_data:
        df_data.extend(table)
    df = pd.DataFrame(df_data[1:], columns=df_data[0])
    return df

def save_to_excel(df_data :pd.DataFrame, excel_path :str) -> None:
    '''

    :param df_data: dataframe数据
    :param excel_path: 输出的表格文件路径
    :return: None
    '''
    # 计算数据行数
    num_rows = len(df_data)
    max_rows_per_sheet = 1000000
    # 如果数据行数超过限制，拆分数据保存到多个工作表
    if num_rows > max_rows_per_sheet:
        num_sheets = -(-num_rows // max_rows_per_sheet)  # 向上取整

        with pd.ExcelWriter(excel_path) as writer:
            for sheet_num in range(num_sheets):
                start_row = sheet_num * max_rows_per_sheet
                end_row = min((sheet_num + 1) * max_rows_per_sheet, num_rows)
                df_part = df_data.iloc[start_row:end_row]
                sheet_name = f'Sheet_{sheet_num + 1}'
                df_part.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        # 数据行数未超过限制，直接保存到一个工作表
        df_data.to_excel(excel_path, index=False)

def check_pdf_path(pdf_path :str) -> bool:
    if not os.path.exists(pdf_path):
        return False
    with open(pdf_path, 'rb') as fp:
        head = fp.read(4)
        if head != b'%PDF':
            return False
    return True

def check_pdf_dir(dir_path :str) -> list:
    if not os.path.exists(dir_path):
        return []
    pdfs = []
    files = os.listdir(dir_path)
    for file in files:
        if file.endswith('.pdf'):
            with open(os.path.join(dir_path,file), 'rb') as fp:
                head = fp.read(4)
                if head == b'%PDF':
                    pdfs.append(os.path.join(dir_path, file))
    return pdfs

def get_params():
    print(f"[yellow]请选择输入模式[1：单文件，2：多文件，其他：退出]：",end='')
    input_mode = input()
    if input_mode == '1':
        while True:
            print("[blue]请输入PDF文件路径：",end='')
            pdf_path = input()
            pdf_path = pdf_path.replace('"', '')
            if check_pdf_path(pdf_path):
                break
            else:
                print(f"[red]输入的PDF文件不存在或不是PDF文件！")
        return {
            "mode": 1,
            "pdf_path": pdf_path
        }
    elif input_mode == '2':
        while True:
            print("[blue]请输入PDF所在文件夹路径：", end='')
            dir_path = input()
            pdf_paths = check_pdf_dir(dir_path)
            if pdf_paths:
                break
            else:
                print(f"[red]输入的目录中没有PDF文件！")
        print(f"[yellow]请选择输出模式[1：每个文件输出一个表格，2：所有文件合并为同一个表格（确保这些pdf表格的表头是一致的），其他：退出]：",end='')
        out_mode = input()
        if out_mode not in ['1','2']:
            sys.exit()
        return {
            "mode": 2,
            "pdf_path": pdf_paths,
            "out_mode": int(out_mode)
        }
    else:
        sys.exit()


def save_single_excel(pdf_path :str):
    print(f"[blue]读取<{os.path.basename(pdf_path)}>中...")
    table_data = read_pdf_tables(pdf_path)
    print(f"[green]读取<{os.path.basename(pdf_path)}>成功！")
    excel_path = pdf_path.replace('.pdf', '.xlsx')
    print(f"[blue]保存<{os.path.abspath(excel_path)}>中...")
    save_to_excel(get_dataframe(table_data), excel_path)
    print(f"[green]保存<{os.path.abspath(excel_path)}>成功！")

def main():
    print('''

            _  __ ____                   _ 
  _ __   __| |/ _|___ \ _____  _____ ___| |
 | '_ \ / _` | |_  __) / _ \ \/ / __/ _ \ |
 | |_) | (_| |  _|/ __/  __/>  < (_|  __/ |
 | .__/ \__,_|_| |_____\___/_/\_\___\___|_|
 |_|                                       Author: WXjzc
''')
    params = get_params()
    mode = params['mode']
    if mode == 1:
        save_single_excel(params['pdf_path'])
    if mode == 2:
        pdf_paths = params['pdf_path']
        out_mode = params['out_mode']
        if out_mode == 1:
            for pdf_path in pdf_paths:
                save_single_excel(pdf_path)
        elif out_mode == 2:
            table_datas = []
            for pdf_path in pdf_paths:
                print(f"[blue]读取<{os.path.basename(pdf_path)}>中...")
                table_data = read_pdf_tables(pdf_path)
                print(f"[green]读取<{os.path.basename(pdf_path)}>成功！")
                table_datas.append(get_dataframe(table_data))
            print(f"[blue]合并表格中....")
            df = pd.concat(table_datas)
            print(f"[green]合并表格成功！")
            dir_path = os.path.dirname(pdf_paths[0])
            excel_path = os.path.abspath(os.path.join(dir_path,"合并.xlsx"))
            print(f"[blue]保存<{excel_path}>中...")
            save_to_excel(df, excel_path)
            print(f"[green]保存<{excel_path}>成功！")
    input("回车退出！")

main()