import os
from base64 import urlsafe_b64decode
from rich import print

def write_data(data, path):
    _dir = os.path.dirname(path)
    if not os.path.exists(_dir):
        os.makedirs(_dir)
    with open(path,'wb') as f:
        f.write(data)

def unpack(pak_path,out_path):
    pak_size = os.path.getsize(pak_path)
    with open(pak_path, 'rb') as fr:
        while True:
            line = fr.readline()
            try:
                line = line.decode()
                file_path = urlsafe_b64decode(line.split(' ')[0]).decode('utf8')
                file_size = line.split(' ')[1].strip()
                if int(file_size) == 0:
                    file_data = b''
                else:
                    file_data = fr.read(int(file_size))
                print(f'[blue]解包文件：{file_path}，文件大小：{file_size}')
                write_data(file_data, os.path.join(out_path,file_path))
                if fr.tell() == pak_size:
                    print(f'[green]解包{os.path.basename(pak_path)}完成')
                    break
            except Exception as e:
                print(f'[red]出现了异常：{e}')
                break

def main():
    print('[yellow]请输入.baksd_pak附件包所在的目录：')
    input_path = input()
    print('[yellow]请输入解包后要导出的目标目录（默认同目录）：')
    out_path = input()
    if not out_path:
        out_path = input_path
    files = os.listdir(input_path)
    for file in files:
        if file.endswith('.baksd_pak'):
            pak_path = os.path.join(input_path,file)
            print(f'[yellow]正在解包{file}')
            unpack(pak_path,out_path)
    print('[green][blod]By WXjzc')

main()