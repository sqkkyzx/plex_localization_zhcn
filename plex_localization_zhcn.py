## python 3
# pip install plexapi
# pip install pypinyin
# 更多中文插件请访问plexmedia.cn

import http.client
import json
import xmltodict as xmltodict
import urllib
from urllib import parse
import pypinyin
from plexapi.server import PlexServer


# 服务器助手函数
def main(token, host, path='', method='GET', get_form_plextv=False, params=None):
    headers = {'X-Plex-Token': token, 'Accept': 'application/json'}
    if get_form_plextv:
        url = 'plex.tv'
        connection = http.client.HTTPSConnection(url)
    else:
        url = host.rstrip('/').replace('http://', '')
        connection = http.client.HTTPConnection(url)
    try:
        if method.upper() == 'GET':
            pass
        elif method.upper() == 'POST':
            headers.update({'Content-type': 'application/x-www-form-urlencoded'})
            pass
        elif method.upper() == 'PUT':
            pass
        elif method.upper() == 'DELETE':
            pass
        else:
            print("Invalid request method provided: {method}".format(method=method))
            connection.close()
            return

        connection.request(method.upper(), path, params, headers)
        response = connection.getresponse()
        r = response.read()
        contenttype = response.getheader('Content-Type')
        # status = response.status
        connection.close()

        if response and len(r):
            if 'application/json' in contenttype:
                return json.loads(r)
            elif 'application/xml' in contenttype:
                return xmltodict.parse(r)
            else:
                return r
        else:
            return r

    except Exception as e:
        connection.close()
        print("Error fetching from Plex API: {err}".format(err=e))
        

tags = {
    "Anime": "动画",     "Action": "动作",     "Mystery": "悬疑",     "Tv Movie":  "电视",     "Animation":       "动画",
    "Crime": "犯罪",     "Family": "家庭",     "Fantasy": "奇幻",     "Disaster":  "灾难",     "Adventure":       "冒险",
    "Short": "短片",     "Horror": "恐怖",     "History": "历史",     "Suspense":  "悬疑",     "Biography":       "传记",
    "Sport": "体育",     "Comedy": "喜剧",     "Romance": "爱情",     "Thriller":  "惊悚",     "Documentary":     "纪录",
    "Music": "音乐",     "Sci-Fi": "科幻",     "Western": "西部",     "Children":  "儿童",     "Martial Arts":    "功夫",
    "Drama": "剧情",     "War":    "战争",     "Musical": "音乐",     "Film-noir": "黑色",     "Science Fiction": "科幻",
    "Food":  "食物",     "War & Politics": "战争与政治"
}


def isChinese(text):
    """判断字符串是否为中文字符"""
    if text == "":
        return True
    for ch in text:
        if '\u4e00' <= ch <= '\u9fff':
            return True
    return False


def convertToPinyin(text):
    """将字符串转换为拼音首字母形式。"""
    str_a = pypinyin.pinyin(text, style=pypinyin.FIRST_LETTER)
    str_b = []
    for i in range(len(str_a)):
        str_b.append(str(str_a[i][0]).upper())
    str_c = ''.join(str_b)
    return str_c


class PLEX:

    def __init__(self, host: str, token: str, actionType: int):
        """
        :param host: 可访问的 plex 服务器地址。例如 http://127.0.0.1:32400/
        :param token: 服务器的 token
        :param actionType: 操作模式。 1为电影；2为电视剧。
        """
        self.host = host
        self.token = token
        self.actionType = actionType

    def listLibrary(self):
        """
        列出库。
        """
        sections = None
        plex = PlexServer(self.host, self.token)
        print(self.actionType)
        if int(self.actionType) == 1:
            sections = [section for section in plex.library.sections() if section.type == "movie"]
        elif int(self.actionType) == 2:
            sections = [section for section in plex.library.sections() if section.type == "show"]
        return sections

    def __convertSortTitle(self, libraryid, ratingkey, title):
        """如果标题排序为中文或为空，则将标题排序转换为中文首字母。"""
        sorttitle = convertToPinyin(title)
        print(f"{title}    : {sorttitle}")
        sorttitle = urllib.parse.quote(sorttitle.encode('utf-8'))
        fetchPlexApi.main(
            host=self.host,
            token=self.token,
            path=f"/library/sections/{libraryid}/all?"
                 f"type={self.actionType}&id={ratingkey}&titleSort.value={sorttitle}&",
            method="PUT"
        )

    def __updataGenre(self, libraryid, ratingkey, title, genre):
        """变更分类标签。"""
        for tag in genre:
            enggenre = tag["tag"]
            if isChinese(enggenre):
                continue
            zh_query = tags.get(tag["tag"])
            if zh_query:
                print(f"{title}    : {enggenre} → {zh_query}")
                zh_query = urllib.parse.quote(zh_query.encode('utf-8'))
                enggenre = urllib.parse.quote(enggenre.encode('utf-8'))
                path = f"/library/sections/{libraryid}/all?" \
                       f"type=1&id={ratingkey}&" \
                       f"genre%5B2%5D.tag.tag={zh_query}&genre%5B%5D.tag.tag-={enggenre}&"
                fetchPlexApi.main(self.token, self.host, path, "PUT")
            else:
                print(f"请在 TAGS 字典中，为 {enggenre} 标签添加对应的中文。")

    def LoopAll(self, libraryid):
        """
        遍历指定媒体库中的每一个媒体。
        """
        todo, start, size = 1, 0, 100
        while todo != 0:
            path = f'/library/sections/{libraryid}/all?' \
                   f'type={self.actionType}&X-Plex-Container-Start={start}&X-Plex-Container-Size={size}'
            metadata: dict = fetchPlexApi.main(self.token, self.host, path)

            total_size = metadata["MediaContainer"]["totalSize"]
            offset = metadata["MediaContainer"]["offset"]
            size = metadata["MediaContainer"]["size"]

            start = start + size
            todo = total_size - offset - size

            for media in metadata["MediaContainer"]["Metadata"]:
                ratingkey = media["ratingKey"]
                title = media["title"]
                titlesort = media.get("titleSort", "")
                genre = media.get('Genre')
                if isChinese(titlesort):
                    self.__convertSortTitle(libraryid, ratingkey, title)
                if genre:
                    self.__updataGenre(libraryid, ratingkey, title, genre)


if __name__ == '__main__':

    URL = input('请输入你的 PLEX 服务器地址 ( 例如 http://127.0.0.1:32400/ )：') or "http://192.168.168.1:32400/"
    TOKEN = input('请输入你的 TOKEN：') or "97TexhuA_rnUbNJgpFSu"
    TYPE = input('请输入操作的库类型，1为电影，2为电视剧：') or 1

    server = PLEX(URL, TOKEN, TYPE)
    print(server.listLibrary())
    sectionId = input("选择要操作的库的 ID 数字:")

    server.LoopAll(sectionId)
