from forlost_sdk_news import *
from NSTools import *
import urllib, requests
from lxml import etree
import time
import logging

logging.basicConfig(level=logging.ERROR,#控制台打印的日志级别
                    filename='url_ERROR.log',
                    filemode='a',
                    format=
                    '%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'
                    #日志格式
                    )

__URL = r'https://www.ltn.com.tw/'
__WEBNAME = 'ltn'
__HOST = r'ltn.com.tw'
PROCESS = ProcessTool()
REDISCLI = RedisCertified('ltn')

def getCatalog():
    tree = PROCESS.pageSourse(__URL)
    catalog_urls = tree.xpath(r'//div[@class="useMobi"]/ul/li/a/@href')
    list = catalog_urls[1:8]
    for url in list:
        name = url.split('/')[-1]
        page_url = urllib.parse.urljoin('https://news.ltn.com.tw/list/breakingnews/', name)
        yield page_url, name

def getAjaxUrl(name):
    ajaxurl = f'https://news.ltn.com.tw/ajax/breakingnews/{name}/'
    for i in range(1, 26):
        url = ajaxurl + f'{i}'
        yield url


def ajaxCotent(url):
    """
    返回json中的图片url和文章url
    :param url:
    :return:
    """

    try:
        jsons = requests.get(url).text

    except:
        print('连接出错,正在重连')
        i = 0
        if i <= 3:
            jsons = requests.get(url).text
            i += 1
        else:
            print("json没有数据")


    urls = json.loads(jsons)
    if urls["data"]:
        if isinstance(urls["data"], list):
            for key in urls["data"]:
                yield key["url"], key["photo_S"]

        elif isinstance(urls["data"], dict):
            for key in urls["data"]:
                yield urls["data"][f"{key}"]["url"], urls["data"][f"{key}"]["photo_S"]
# key["data"][int(key)]["url"]



def nesContent(url):
    print(url)
    tree = PROCESS.pageSourse(url)
    # 图片xpath
    image = tree.xpath(r'//div[@class="photo boxTitle"]/a/img/@src')
    image_info = tree.xpath(r'//div[@class="photo boxTitle"]/a/img/@title')
    # 文本xpath,去取文本的空白格
    texts = tree.xpath(r'//div[@class="text boxTitle boxText"]/p')
    contents =[]
    for text in texts:
        p = etree.tostring(text, encoding="utf-8", pretty_print=True, method="html").decode('utf-8')
        contents.append(p)
    content = ''.join(''.join(contents).split())

    # # 时间 转换为时间戳
    times = tree.xpath(r'//span[@class="time"]/text()')[0].strip()
    # # 作者
    author = tree.xpath(r'//div[@class="text boxTitle boxText"]/h4/text()')
    # 标题
    title = tree.xpath(r'//div[@class="whitecon"]/h1/text()')[0]

    return content, str(times), author, title, (image, image_info,)

def sportsNew(url):
    print(url)
    tree = PROCESS.pageSourse(url)
    # 图片xpath
    image = tree.xpath(r'//div[@class="news_p"]/div/p/span//img/@src')
    image_info = tree.xpath(r'//div[@class="news_p"]//span[@class="ph_d"]/text()')
    # 文本xpath,去取文本的空白格
    texts = tree.xpath(r'//div[@class="news_p"]//p')
    contents = []
    for text in texts:
        p = etree.tostring(text, encoding="utf-8", pretty_print=True, method="html").decode('utf-8')
        contents.append(p)
    content = ''.join(''.join(contents).split())

    # # 时间 转换为时间戳
    try:
        times = tree.xpath(r'//div[@class="c_box"]/div/text()')[0]
    except:
        times = []
    # # 作者
    author = tree.xpath(r'//div[@class="text boxTitle boxText"]/h4/text()')
    # 标题
    try:
        title = tree.xpath(r'//div[@class="news_content"]/h1/text()')[0]
    except:
        title = tree.xpath(r'//div[@class="news_content"]/h1/text()')
        print('title为空')
        print(title)

    return content, str(times), author, title, (image, image_info,)


def ecNew(url):
    print(url)
    tree = PROCESS.pageSourse(url)
    # 图片xpath
    image = tree.xpath(r'//div[@class="text"]//span[@class="ph_i"]/img/@src')
    image_info = tree.xpath(r'//div[@class="text"]//span[@class="ph_d"]/text()')
    # 文本xpath,去取文本的空白格
    texts = tree.xpath(r'//div[@class="text"]/p')
    contents = []
    for text in texts:
        p = etree.tostring(text, encoding="utf-8", pretty_print=True, method="html").decode('utf-8')
        contents.append(p)
    content = ''.join(''.join(contents).split())

    # # 时间 转换为时间戳
    times = tree.xpath(r'//div[@class="text"]/span/text()')[0]
    # # 作者
    author = tree.xpath(r'//div[@class="text boxTitle boxText"]/h4/text()')
    # 标题
    title = tree.xpath(r'//div[@class="whitecon boxTitle"]/h1/text()')[0].strip()

    return content, str(times), author, title, (image, image_info,)


def entNews(url):
    print(url)
    tree = PROCESS.pageSourse(url)
    # 图片xpath
    image = tree.xpath(r'//span[@class="ph_i"]/img/@src')
    image_info = tree.xpath(r'//span[@class="ph_d"]/text()')
    # 文本xpath,去取文本的空白格
    texts = tree.xpath(r'//div[@class="news_content"]/p')
    contents = []
    for text in texts:
        p = etree.tostring(text, encoding="utf-8", pretty_print=True, method="html").decode('utf-8')
        contents.append(p)
    content = ''.join(''.join(contents).split())

    # # 时间 转换为时间戳
    times = tree.xpath(r'//div[@class="date"]/text()')[0].strip()
    # # 作者
    author = tree.xpath(r'//div[@class="author"]/text()')[0]
    # 标题
    try:
        title = tree.xpath(r'//div[@class="news_content"]/h1/text()')[0].strip()
    except:
        title = tree.xpath(r'//div[@class="news_content"]/h1/text()')
        print('title为空')
        print(title)

    return content, str(times), author, title, (image, image_info,)

def talkNews(url):
    print(url)
    tree = PROCESS.pageSourse(url)
    # 图片xpath
    image = tree.xpath(r'//span[@class="ph_i"]/img/@src')
    image_info = tree.xpath(r'//span[@class="ph_d"]/text()')
    # 文本xpath,去取文本的空白格
    texts = tree.xpath(r'//div[@class="text boxTitle boxText"]/p')
    contents =[]
    for text in texts:
        p = etree.tostring(text, encoding="utf-8", pretty_print=True, method="html").decode('utf-8')
        contents.append(p)
    content = ''.join(''.join(contents).split())

    # # 时间 转换为时间戳
    try:
        times = tree.xpath(r'//div[@class="mobile_none"]/text()')[0].strip()
    except:
        times = tree.xpath(r'//div[@class="writer_date"]/text()')[0].strip()
    # # 作者
    try:
        author = tree.xpath(r'//div[@class="writer boxTitle"]/a/span[2]/text()')[0].strip()
    except:
        author = tree.xpath(r'//div[@class="cont"]/p/text())')[0].strip()

    # 标题
    title = tree.xpath(r'//div[@class="conbox"]/h1/text()')[0]

    return content, str(times), author, title, (image, image_info,)



def newsMain():
    for url, name in getCatalog():
        for i in getAjaxUrl(name):
            for j in ajaxCotent(i):
                url, image = j
                if "sports." in url :
                    fp = REDISCLI.urlFingerPrint(url)
                    if REDISCLI.urlAdd(fp):
                        comeurl = url
                        time.sleep(0.5)
                        _text, _times, _author, title, _image = sportsNew(url)
                        other_info = PROCESS.authorPacket(_author)
                        yuantime = PROCESS.timeConvert(_times)
                        file = PROCESS.imageFile(_image)
                        content = _text
                        yield comeurl, title, other_info, yuantime, file, content
                elif "ec." in url:
                    fp = REDISCLI.urlFingerPrint(url)
                    if REDISCLI.urlAdd(fp):
                        comeurl = url
                        time.sleep(0.5)
                        _text, _times, _author, title, _image = ecNew(url)
                        other_info = PROCESS.authorPacket(_author)
                        yuantime = PROCESS.timeConvert(_times)
                        file = PROCESS.imageFile(_image)
                        content = _text
                        yield comeurl, title, other_info, yuantime, file, content
                elif "ent." in url:
                    fp = REDISCLI.urlFingerPrint(url)
                    if REDISCLI.urlAdd(fp):
                        comeurl = url
                        time.sleep(0.5)
                        _text, _times, _author, title, _image = entNews(url)
                        other_info = PROCESS.authorPacket(_author)
                        yuantime = PROCESS.timeConvert(_times)
                        file = PROCESS.imageFile(_image)
                        content = _text
                        yield comeurl, title, other_info, yuantime, file, content
                elif "talk." in url:
                    fp = REDISCLI.urlFingerPrint(url)
                    if REDISCLI.urlAdd(fp):
                        comeurl = url
                        time.sleep(0.5)
                        _text, _times, _author, title, _image = talkNews(url)
                        other_info = PROCESS.authorPacket(_author)
                        yuantime = PROCESS.timeConvert(_times)
                        file = PROCESS.imageFile(_image)
                        content = _text
                        yield comeurl, title, other_info, yuantime, file, content
                else:
                    fp = REDISCLI.urlFingerPrint(url)
                    if REDISCLI.urlAdd(fp):
                        comeurl = url
                        time.sleep(0.5)
                        try:
                            _text, _times, _author, title, _image = nesContent(url)
                            other_info = PROCESS.authorPacket(_author)
                            yuantime = PROCESS.timeConvert(_times)
                            file = PROCESS.imageFile(_image)
                            content = _text
                            yield comeurl, title, other_info, yuantime, file, content
                        except Exception as ERR:
                            print(ERR)
                            with open('url.txt','a') as file:
                                file.write(comeurl)

if __name__ == '__main__':
    # 这一长串就是得到ajax中的文章url，
    for i in newsMain():
        comeurl, title, other_info, yuantime, file, content = i
        post_news(
            title=title, content=content, otherInfo=other_info,
            files=file, comeurl=comeurl, webhost=__HOST,
            yuantime=yuantime, downworkid='	b22de95e-a115-435a-9864-3407a267b9ea', webname=__WEBNAME
        )
        time.sleep(1)
    print('新闻爬取完毕')