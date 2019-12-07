from forlost_sdk_news import *
from NSTools import *
import urllib, requests
from lxml import etree
import time
import logging

# logging.basicConfig(level=logging.ERROR,#控制台打印的日志级别
#                     filename='chinatimes_ERROR.log',
#                     filemode='a',
#                     format=
#                     '%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'
#                     #日志格式
#                     )

__URL = r'https://www.chinatimes.com/realtimenews/?chdtv'
__WEBNAME = 'chinatimes'
__HOST = r'chinatimes.com'
PROCESS = ProcessTool()
REDISCLI = RedisCertified('chinatimes')

urllist = [
    "https://www.chinatimes.com/realtimenews/260407",
    "https://www.chinatimes.com/realtimenews/260405",
    "https://www.chinatimes.com/realtimenews/260405",
    "https://www.chinatimes.com/realtimenews/260415",
    "https://www.chinatimes.com/realtimenews/260404",
    "https://www.chinatimes.com/realtimenews/260403",
    "https://www.chinatimes.com/realtimenews/260410",
    "https://www.chinatimes.com/realtimenews/260408",
    "https://www.chinatimes.com/realtimenews/260409",
    "https://www.chinatimes.com/realtimenews/260417",
    "https://www.chinatimes.com/realtimenews/260412"
]

def catalogProcess():
    for i in urllist:
        for num in range(2, 11):
            url = i + f"?page={num}" + "&chdtv"
            yield url

def getpage(url):
    source = PROCESS.pageSourse(url)
    page_urls = source.xpath(r'//ul[@class="vertical-list list-style-none"]/li//h3/a/@href')
    for url in page_urls:
        url = r"https://www.chinatimes.com" + url
        yield url


def newsUrl():
    pass


def newsContent(url):
    print(url)
    tree = PROCESS.pageSourse(url)
    # 图片xpath
    image = tree.xpath(r'//div[@class="photo-container"]/img/@src')
    image_info = tree.xpath(r'//div[@class="photo-container"]/img/@alt')
    # 文本xpath,去取文本的空白格
    texts = tree.xpath(r'//div[@class="article-body"]/p')
    contents =[]
    for text in texts:
        p = etree.tostring(text, encoding="utf-8", pretty_print=True, method="html").decode('utf-8')
        contents.append(p)
    content = ''.join(''.join(contents).split())

    # # 时间 转换为时间戳
    try:
        times = tree.xpath(r'//div[@class="meta-info-wrapper"]/div/time/@datetime')[0]
    except:
        times = tree.xpath(r'//div[@class="meta-info-wrapper"]/div/time/@datetime')
        print(times)
    # # 作者
    try:
        author = tree.xpath(r'//div[@class="author"]/a/text()')[0]
    except:
        author = tree.xpath(r'//div[@class="meta-info-wrapper"]//div[@class="author"]/text()')[0].strip()
    # 标题
    title = tree.xpath(r'//div[@class="article-wrapper"]//h1/text()')[0]

    return content, str(times), author, title, (image, image_info,)

def chinatimeMain():
    for master_url in catalogProcess():
        for slave_url in getpage(master_url):
            time.sleep(0.2)
            # print(slave_url)
            # text, _times, _author, title, _image = newsContent(slave_url)
            # print('content\t', text)
            # print('time\t', _times)
            # print('author\t', _author)
            # print('title\t', title)
            # print('file\t', _image)
            fp = REDISCLI.urlFingerPrint(slave_url)
            if REDISCLI.urlAdd(fp):
                comeurl = slave_url
                time.sleep(1)
                _text, _times, _author, title, _image = newsContent(slave_url)
                other_info = PROCESS.authorPacket(_author)
                yuantime = PROCESS.timeConvert(_times)
                file = PROCESS.imageFile(_image)
                content = _text
                yield comeurl, title, other_info, yuantime, file, content


if __name__ == '__main__':
    while True:
        for i in chinatimeMain():
            comeurl, title, other_info, yuantime, file, content = i
            post_news(
                title=title, content=content, otherInfo=other_info,
                files=file, comeurl=comeurl, webhost=__HOST,
                yuantime=yuantime, downworkid='17dc5a9a-a7fe-411f-8dbe-a50255308442', webname=__WEBNAME
            )
            time.sleep(1)
        print('休息一下')
        time.sleep(120)
    #
    #     # print('comeurl\t', comeurl)
    #     # print('title\t', title)
    #     # print('other_info\t', other_info)
    #     # print('yuantime\t', yuantime)
    #     # print('file\t', file)
    #     # print('content\t', content)
    # content, times, author, title, image = newsContent('https://www.chinatimes.com/realtimenews/20191113003823-260404')
    # print(content)
    # print(times)
    # print(author)
    # print(title)
    # print(image)