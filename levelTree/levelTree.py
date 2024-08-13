import time
import csv
import os
from rich import print

def read_data(file):
    '''读取为字典格式'''
    dic = {}
    try:
        with open(file,'r',encoding='utf8') as fr:
            lines = fr.readlines()
            for line in lines:
                data = line.replace('\n','').split('\t')
                dic[data[0]] = data[1]
    except UnicodeDecodeError:
        with open(file,'r',encoding='gbk') as fr:
            lines = fr.readlines()
            for line in lines:
                data = line.replace('\n','').split('\t')
                dic[data[0]] = data[1]
    except Exception as e:
        print(e)
    return dic

def get_parents(uid,level_data,lst:list):
    '''递归获取所有上级'''
    if level_data[uid] == '':
        # 通过上级ID为空判断是否到头，所以要确保除了顶层用户外，所有用户都有上级
        return lst
    lst.append(level_data[uid])
    return get_parents(level_data[uid],level_data,lst)

def calculate_subordinate_info(user_tree, user_id):
    '''计算下线数量和下线层级'''
    if user_id not in user_tree:
        return 0, 0  # 如果没有下线，层数和数量都是0

    max_depth = 0
    total_subordinates = 0

    for sub_id in user_tree[user_id]:
        sub_count, sub_depth = calculate_subordinate_info(user_tree, sub_id)
        total_subordinates += sub_count + 1  # 加1是因为直接下线也要算
        max_depth = max(max_depth, sub_depth + 1)
    
    return total_subordinates, max_depth

def build_tree(level_data :dict):
    '''创建下线层级树'''
    tree = {}
    for key,value in level_data.items():
        user_id, superior_id = key, value
        if superior_id not in tree:
            tree[superior_id] = []
        tree[superior_id].append(user_id)
    return tree

def main():
    print(r'''
  _                _ _____              
 | | _____   _____| |_   _| __ ___  ___ 
 | |/ _ \ \ / / _ \ | | || '__/ _ \/ _ \
 | |  __/\ V /  __/ | | || | |  __/  __/
 |_|\___| \_/ \___|_| |_||_|  \___|\___|
                                        Author: WXjzc
''')
    print('[bold blue][!]请确保只有顶层用户的上级ID为空值，其他用户必须要有上级')
    print('[yellow][+]请拖入文件，只包含id和上级id，以制表符分割，无需表头：')
    file = input()
    start_time = time.time()
    level_data = read_data(file.replace('"',''))
    total = []
    user = {}
    for v in level_data.keys():
        # 获取用户所有上级，计算所处层级和推荐链条
        lst = get_parents(v,level_data,[v])
        所处层级 = len(lst)
        tmp = lst[::-1]
        推荐链条 = '->'.join(tmp)
        total.append(推荐链条)
        user.update({
            v:{
                "上级ID":level_data[v],
                "所处层级":所处层级,
                "推荐链条":推荐链条
            }
        })
    tree = build_tree(level_data)
    for v in level_data.keys():
        # 获取用户下线数量和下线层数
        下线数量,下线层数 = calculate_subordinate_info(tree,v)
        user[v].update({
            "下线数量":下线数量,
            "下线层数":下线层数
        })
    out_put = os.path.join(os.path.dirname(os.path.abspath(file)),'tree.csv')
    with open(out_put,'w',newline='',encoding='utf8') as fw:
        writer = csv.writer(fw)
        writer.writerow(['ID','上级ID','所处层级','下线层数','下线数量','推荐链条'])
        for key in user.keys():
            writer.writerow([
                key,
                user[key]['上级ID'],
                user[key]['所处层级'],
                user[key]['下线层数'],
                user[key]['下线数量'],
                user[key]['推荐链条'],
                ])
    print(f'[green][√]处理完成，耗时{time.time()-start_time}秒')
    input()

main()