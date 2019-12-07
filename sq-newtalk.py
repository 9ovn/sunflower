from forlost_sdk_news import *
from NSTools import *
import urllib
from lxml import etree
import time
from bs4 import BeautifulSoup as bs
import re

__URL = r'https://newtalk.tw/news/summary/today'
__WEBNAME = 'newtalks'
__HOST = r'newtalk.tw'
PROCESS = ProcessTool()
REDISCLI = RedisCertified('newtalk')


def getCatalog():
    source = PROCESS.pageSourse(__URL)
    lis = source.xpath('//*[@id="News"]/ul/li/a/@href')
    catNmae = source.xpath('//*[@id="News"]/ul/li/a/text()')
    catalog_dict = dict(zip(catNmae, lis))
    today = catalog_dict['總覽']
    topics = catalog_dict['議題']
    del catalog_dict['總覽']
    del catalog_dict['議題']
    return catalog_dict, today, topics

def getListUrl(url):
    try:
        source = PROCESS.pageSourse(url)
        pageurl = source.xpath('//*[@id="left_column"]/div[6]/div/a[last()-1]/@href')[0]
        pagenum = int(re.findall(r'\/(\d{1,4})', pageurl)[-1])
        for i in range(1, pagenum+1):
            new_url = url + f'/{i}'
            yield new_url
    except Exception as Err:
        print(Err)

def getNewsUrl(url):
    """
    解析页面url
    :param url:
    :return:
    """
    try:
        tree = PROCESS.pageSourse(url)
        urls = tree.xpath(r'//div[@id="category"]/div[@class="news-list-item clearfix "]/div/a[1]/@href')
        for url in urls:
            yield url
    except Exception as Err:
        print(Err)

def getTodayUrl(url):
    """
    特殊页面总览的页面获取
    :param url:
    :return:
    """
    tree = PROCESS.pageSourse(url)
    urls = tree.xpath(r'//div[@class="news-list-item clearfix"]/div[1]/a/@href')
    for url in urls:
        yield url

def newsContent(url):
    tree = PROCESS.pageSourse(url)
    # 图片xpath
    images = tree.xpath(r'//div[@id="news_content"]//img/@src')
    image=[]
    for i in images:
        if 'https:' in i:
            image.append(i)
        else:
            url = 'https:' + i
            image.append(url)

    image_infos = tree.xpath(r'//div[@id="news_content"]//img/@alt')
    image_info = list(map(lambda x: x.strip(), image_infos))
    # 文本xpath,去取文本的空白格
    texts = tree.xpath(r'//div[@id="news_content"]//p')
    txt = tree.xpath(r'//div[@id="news_content"]//p/text()')
    contents =[]
    for text in texts:
        p = etree.tostring(text, encoding="utf-8", pretty_print=True, method="html").decode('utf-8')
        contents.append(p)
    content = ''.join(''.join(contents).split())

    # # 时间 转换为时间戳
    times = tree.xpath(r'//div[@id="contentTop"]/div/div[@class="content_date"]/text()')[-1].replace('|', '')
    time = re.findall(r'(\d+\.\d+\.\d+\s+\d+\:\d+)', times)[0]
    # # 作者
    author = tree.xpath(r'//div[@id="contentTop"]//a/text()')[0]
    # 标题
    title = tree.xpath(r'//div[@id="left_column"]/h1/text()')[0]

    return content, str(time), author, title, (image, image_info,)

def newsMain(i):
    try:
        getCatalog, *_ = i
        for url in getCatalog.values():
            for url_1 in getListUrl(url):
                print('全站爬取' + str(url_1))
                time.sleep(0.2)
                for i in getNewsUrl(url_1):
                    print(i)
                    fp = REDISCLI.urlFingerPrint(i)
                    if REDISCLI.urlAdd(fp):
                        comeurl = i
                        time.sleep(0.5)
                        _text, _times, _author, title, _image = newsContent(i)
                        other_info = PROCESS.authorPacket(_author)
                        yuantime = PROCESS.timeConvert(_times)
                        file = PROCESS.imageFile(_image)
                        content = _text
                        yield comeurl, title, other_info, yuantime, file, content
                    else:
                        print('url已存在')
    except Exception as Err:
        print(Err)

def todayNews(i):
    _, today, _ = i
    print(today)
    for url in getTodayUrl(today):
        print(url)
        time.sleep(0.2)
        fp = REDISCLI.urlFingerPrint(url)
        if REDISCLI.urlAdd(fp):
            comeurl = url
            time.sleep(0.5)
            _text, _times, _author, title, _image = newsContent(url)
            other_info = PROCESS.authorPacket(_author)
            yuantime = PROCESS.timeConvert(_times)
            file = PROCESS.imageFile(_image)
            content = _text
            yield comeurl, title, other_info, yuantime, file, content
        else:
            print('url已存在')


if __name__ == "__main__":
    a = getCatalog()
    for i in todayNews(a):
        comeurl, title, other_info, yuantime, file, content = i
        post_news(
            title=title, content=f'{content}', otherInfo=other_info,
            files=file, comeurl=comeurl, webhost=__HOST,
            yuantime=yuantime, downworkid='51f57d4f-9f93-417a-b1b3-e649d1034b91',
            webname=__WEBNAME
        )
    print('今日新闻已经抓取完毕')


    time.sleep(20)

    while True:
        for i in newsMain(a):
            comeurl, title, other_info, yuantime, file, content = i
            post_news(
                title=title, content=f'{content}', otherInfo=other_info,
                files=file, comeurl=comeurl, webhost=__HOST,
                yuantime=yuantime, downworkid='51f57d4f-9f93-417a-b1b3-e649d1034b91',
                webname=__WEBNAME
            )
        time.sleep(240)