import requests
import datetime
import os
from hashlib import md5
import sqlite3
from rich import print

headers = {
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
    "Sec-Fetch-Site": "same-origin" ,
    "Sec-Fetch-Mode": "cors" ,
    "Sec-Fetch-Dest": "empty" ,
    "Sec-Ch-Ua-Platform": "Windows" ,
    "Sec-Ch-Ua-Mobile": "?0" ,
    "Sec-Ch-Ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Microsoft Edge";v="128"',
    "Referer": "https://www.douyin.com/" ,
    "Priority": "u=1, i" ,
    "Cache-Control": "no-cache" ,
    "Accept-language": "zh-CN,zh;q=0.9,en;q=0.8" ,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "upgrade-insecure-requests":"1",
    "Cookie": ""
}

def _md5(data):
    mymd5 = md5()
    mymd5.update(data.encode('utf-8'))
    return mymd5.hexdigest()

def save(downloadDir,file,data):

    if os.path.exists(downloadDir) == False:
        os.makedirs(downloadDir)
    with open(os.path.join(downloadDir,file),'wb') as fw:
        fw.write(data)


def config(headers):
    import json
    with open('./固定/config.json','rb') as fr:
        data = json.loads(fr.read())
        headers["User-Agent"] = data["ua"]
        headers["Cookie"] = data["cookie"]
        headers["Referer"] = data["referer"]
        downloadDir = data["downloadDir"]
        urls = data["urls"]
    return downloadDir,urls


downloadDir,urls = config(headers)

connect = sqlite3.connect(os.path.join(downloadDir,'done.db'))
cursor = connect.cursor()
sql = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
cursor.execute(sql)
done_data = cursor.fetchall()
if done_data == []:
    sql = "CREATE TABLE done(hash text);"
    cursor.execute(sql)
sql = "select hash from done;"
cursor.execute(sql)
ret = cursor.fetchall()
done_data = [i[0] for i in ret]
for url in urls:
    response = requests.get(url,headers=headers)
    if response.status_code == 200:
        try:
            aweme_list = response.json().get("aweme_list")
            for aweme in aweme_list:
                desc = aweme.get('desc')
                aweme_id = aweme.get('aweme_id')
                create_time = aweme.get('create_time')
                statistics = aweme.get('statistics')
                likes = statistics.get('digg_count')
                comments = statistics.get('comment_count')
                shares = statistics.get('share_count')
                collects = statistics.get('collect_count')
                author = aweme.get('author')
                author_uid = author.get('uid')
                author_name = author.get('nickname')
                video = aweme.get('video')
                video_url = video.get('play_addr').get('url_list')[-1]
                cover_url = video.get('cover').get('url_list')[-1]
                text = f"""视频ID:{aweme_id}
视频描述:{desc}
作者:{author_name} 
作者id:{author_uid} 
视频地址:{video_url} 
封面地址:{cover_url} 
创建时间:{datetime.datetime.fromtimestamp(create_time)}
点赞数:{likes} 
评论数:{comments} 
分享数:{shares} 
收藏数:{collects}
"""             
                ident = _md5(str(aweme_id)+str(author_uid)+str(create_time))
                if ident in done_data:
                    print(f'[yellow][+]《{desc}》已经处理过，跳过！')
                    continue
                save_path = os.path.join(downloadDir,desc.strip()+str(aweme_id))
                save(save_path,'信息.txt',text.encode())
                video_res = requests.get(video_url)
                cover_url = requests.get(cover_url)
                save(save_path,'视频.mp4',video_res.content)
                cover_ext = cover_url.headers.get("Content-Type").replace('image/','')
                save(save_path,f'封面.{cover_ext}',cover_url.content)
                print(f'[green][√]《{desc}》保存成功！')
                sql = f'insert into done values("{ident}")'
                cursor.execute(sql)
                connect.commit()
        except Exception as e:
            print(f'[red][×]处理{url}时遇到问题，目标视频是《{desc}》，异常信息：{str(e)}')
            with open(os.path.join(downloadDir,'error.log'),'a',encoding='utf8') as fw:
                fw.write(f'处理{url}时遇到问题，目标视频是{desc}，异常信息：{str(e)}')
                fw.write('\n')
