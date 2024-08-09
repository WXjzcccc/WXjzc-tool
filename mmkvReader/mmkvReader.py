import mmkv
import os
from rich import print

class mmkvReader:

    def __init__(self,path:str):
        if os.path.exists(path):
            if os.path.isdir(path):
                mmkv.MMKV.initializeMMKV(path)
                self.path = path
                self.file = False
                self.fileName = ''
            else:
                mmkv.MMKV.initializeMMKV(os.path.dirname(path))
                self.path = os.path.dirname(path)
                self.file = True
                self.fileName = os.path.basename(path)
        else:
            print('[red][-]输入的路径不正确！')
            exit(-1)

    def listObjects(self) -> list:
        '''获取目录下的文件'''
        lst = []
        if not self.file:
            files = os.listdir(self.path)
            for file in files:
                if not file.endswith('.crc'):
                    lst.append(file)
        return lst

    def getObject(self,name:str,cryptKey :str=''):
        '''指定存储数据的文件，返回可读取的对象'''
        if cryptKey != '':
            # 处理加密的内容
            kv = mmkv.MMKV(name,cryptKey=cryptKey)
        else:
            kv = mmkv.MMKV(name)
        return kv
    
    def getAllTypeValue(self,kv,key:str):
        '''由于无法进行类型判断，因此获取每个键的所有类型的值'''
        dic = {
            'bool': kv.getBool(key),
            'int32': kv.getInt(key),
            'uint32': kv.getUInt(key),
            'int64' : kv.getLongInt(key),
            'uint64' : kv.getLongUInt(key),
            'float' : kv.getFloat(key),
            'bytes' : kv.getBytes(key)
        }
        try:
            dic.update({'string' : kv.getString(key)})
        except:
            pass
        return dic

    def getObjectAllValue(self,kv):
        '''获取所有值'''
        keys = kv.keys()
        dic = {}
        for key in keys:
            dic[key] = self.getAllTypeValue(kv,key)
        return dic
    
    def getDirAllValue(self):
        '''获取mmkv目录下所有文件的所有键值，但是不支持加密，因为不同文件可以使用不同的密钥'''
        if not self.file:
            dic = {}
            files = os.listdir(self.path)
            for file in files:
                if not file.endswith('.crc'):
                    try:
                        kv = self.getObject(file)
                        dic[file] = self.getObjectAllValue(kv)
                    except:
                        print(f'[red][-]{file}读取异常!')
        else:
            kv = self.getObject(self.fileName)
            return self.getObjectAllValue(kv)
        return dic


if __name__ == '__main__':
    print('''
                     _           ____                _           
 _ __ ___  _ __ ___ | | ____   _|  _ \ ___  __ _  __| | ___ _ __ 
| '_ ` _ \| '_ ` _ \| |/ /\ \ / / |_) / _ \/ _` |/ _` |/ _ \ '__|
| | | | | | | | | | |   <  \ V /|  _ <  __/ (_| | (_| |  __/ |   
|_| |_| |_|_| |_| |_|_|\_\  \_/ |_| \_\___|\__,_|\__,_|\___|_|   
                                                                 Author: WXjzc
''')
    print('[yellow][+]请输入mmkv目录的路径，或是指定的文件的路径（请确保crc文件在同一目录）：')
    input_file = input()
    if os.path.isdir(input_file):
        reader = mmkvReader(input_file)
        while True:
            print('''[yellow][+]请选择模式：
            [green]【1】输出目录下所有文件中的键值;
            [green]【2】列出目录下的可以查看的文件;
            [green]【3】输入要查看的文件名，只输出这个文件的内容,如果密码输入错误，必须重启程序后再次输入；
            [green]【4】退出。
''')
            input_kv = input()
            if input_kv == '4':
                break
            elif input_kv == '1':
                print(reader.getDirAllValue())
            elif input_kv == '2':
                print(reader.listObjects())
            elif input_kv == '3':
                print('[yellow][+]请输入文件名：')
                name = input()
                lst = reader.listObjects()
                if name not in lst:
                    print('[red][-]输入错误')
                    continue
                print('[blue][+]请输入mmkv的加密密钥，如未加密请直接回车：')
                input_cipher = input()
                kv = reader.getObject(name,input_cipher)
                print(reader.getObjectAllValue(kv))
    else:
        reader = mmkvReader(input_file)
        print('[blue][+]请输入mmkv的加密密钥，如未加密请直接回车：')
        input_cipher = input()
        kv = reader.getObject(reader.fileName,input_cipher)
        print(reader.getObjectAllValue(kv))
        print('[green][+]按任意键退出')
        input()