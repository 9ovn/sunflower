from NSTools import *
import urllib
from lxml import etree
import time
from forlost_sdk_news import *
from bs4 import BeautifulSoup
import requests

__URL = r'https://udn.com/news/breaknews/1/99#breaknews'
__WEBNAME = r'udn'
__HOST = r'udn.com'
PROCESS = ProcessTool()
REDISCLI = RedisCertified('udn')

def getUrl():
    # 列表页
    source = PROCESS.pageSourse(__URL)
    catalog_urls = source.xpath(r'//*[@id="breaknews_body"]/dl/dt/a[1]/@href')
    for url in catalog_urls:
        url = urllib.parse.urljoin('https://udn.com', url)
        yield url

def getAjaxurl():
    micrtime = int(round(time.time()) * 1000)
    flag = 1
    i = 1
    while flag:
        i += 1
        url = f'https://udn.com/news/get_breaks_article/{i}/1/99?_={micrtime}'
        tree = PROCESS.pageSourse(url)
        if len(tree):
            urls = tree.xpath(r'//dt/a[1]/@href')
            for url in urls:
                url = 'https://udn.com' + url
                yield url
        else:
            flag = 0

def newsContent(url):
    # 信息页面的抓取
    tree = PROCESS.pageSourse(url)
    # 图片xpath
    image = tree.xpath(r'//div[@id="story_body_content"]//figure/a/img/@src')
    image_info = tree.xpath(r'//div[@id="story_body_content"]//figure//figcaption/text()')
    # 文本xpath,去取文本的空白格
    texts = tree.xpath(r'//div[@id="story_body_content"]/p')
    contents =[]
    for text in texts:
        p = etree.tostring(text, encoding="utf-8", pretty_print=True, method="html").decode('utf-8')
        contents.append(p)
    content = ''.join(''.join(contents).split())

    # # 时间 转换为时间戳
    times = tree.xpath(r'//div[@id="story_body_content"]//div[@class="story_bady_info_author"]/span/text()')[0]
    # # 作者
    author = tree.xpath(r'//div[@id="story_body_content"]//div[@class="story_bady_info_author"]/a/text()')
    # 标题
    try:
        title = tree.xpath(r'//div[@id="story_body_content"]/h1/text()')[0].strip()
    except:
        title = tree.xpath(r'//div[@id="story_body_content"]/h1/text()')
        print(title)
        print('title出错')
    return content, str(times), author, title, (image, image_info,)

def main():
    for url in getAjaxurl():
        fp = REDISCLI.urlFingerPrint(url)
        if REDISCLI.urlAdd(fp):
            comeurl = url
            print(comeurl)
            _text, _times, _author, title, _image = newsContent(url)
            other_info = PROCESS.authorPacket(_author)
            yuantime = PROCESS.timeConvert(_times)
            file = PROCESS.imageFile(_image)
            content = _text
            yield comeurl, title, other_info, yuantime, file, content

        else:
            print('url已存在')


if __name__ == "__main__":
    for i in main():
        comeurl, title, other_info, yuantime, file, content = i
        post_news(
            title=title, content=f'{content}', otherInfo=other_info,
            files=file, comeurl=comeurl, webhost=__HOST,
            yuantime=yuantime, downworkid='7bae4bba-af8f-45b3-988c-a4ba03604dca',
            webname=__WEBNAME
        )

    while True:
        for i in getUrl():
            fp = REDISCLI.urlFingerPrint(i)
            if REDISCLI.urlAdd(fp):
                comeurl = i
                _text, _times, _author, title, _image = newsContent(i)
                other_info = PROCESS.authorPacket(_author)
                yuantime = PROCESS.timeConvert(_times)
                file = PROCESS.imageFile(_image)
                content = _text

                post_news(
                    title=title, content=content, otherInfo=other_info,
                    files=file, comeurl=comeurl, webhost=__HOST,
                    yuantime=yuantime, downworkid='7bae4bba-af8f-45b3-988c-a4ba03604dca', webname=__WEBNAME
                )
        time.sleep(60)
