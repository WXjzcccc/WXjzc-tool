import plyvel
from rich import print
import os

print('''
 _                _     _ _     ____                _           
| | _____   _____| | __| | |__ |  _ \ ___  __ _  __| | ___ _ __ 
| |/ _ \ \ / / _ \ |/ _` | '_ \| |_) / _ \/ _` |/ _` |/ _ \ '__|
| |  __/\ V /  __/ | (_| | |_) |  _ <  __/ (_| | (_| |  __/ |   
|_|\___| \_/ \___|_|\__,_|_.__/|_| \_\___|\__,_|\__,_|\___|_|   
                                                                Author: WXjzc
''')
# 打开 LevelDB 数据库
while True:
    print('[yellow][+]请输入要查看的leveldb路径（文件夹）：',end='')
    leveldb_file = input()
    if not (os.path.exists(leveldb_file) and os.path.isdir(leveldb_file)):
        print('[red][×]路径不正确！')
    else:
        break
db = plyvel.DB(leveldb_file, create_if_missing=False)
plyvel.repair_db(leveldb_file)
# 读取数据
dic = {}
for key, value in db:
    dic[key] = value
print(dic)
# 关闭数据库
db.close()
print('[green][√]按任意键退出')
input()