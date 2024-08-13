import uuid
import random

lst = [uuid.uuid4()]
with open('out.txt','w') as fw:
    fw.write(str(lst[0])+'\t\n')
    for i in range(1000000):
        uid = uuid.uuid4()
        fw.write(str(uid)+'\t'+str(random.choice(lst))+'\n')
        lst.append(uid)