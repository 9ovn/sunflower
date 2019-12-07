import requests
from lxml import etree
import urllib
import time, datetime
from PIL import Image
from io import BytesIO
import base64
import hashlib
from forlost_sdk import *
from forlost_sdk_news import *
import threading
from pymysql import connect
import redis

"""
task: 编写通用模块！
1. 时间转换时间戳函数(毫秒级)
2. 上传函数
3. SQL注入函数（主要作用是url去重）/ 或者用redis set()
4. 
"""

# 抓取网站的主机
_HOST = "tvbs.com.tw"

# 抓取新闻网站的名字
__WEBNAME = "TVBS"

# 要抓取的URL地址
_URL = r"https://news.tvbs.com.tw"

# 本文本编写结束
HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"
}


def page_sourse(url):
    """
    解析指定url
    :param url: 需要爬取的url地址
    :return: 返回一个解析过的HTML结构
    """
    try:
        response = requests.get(url=url, headers=HEADERS)
        tree = etree.HTML(response.content.decode('utf-8'))
        return tree

    except Exception as Err:
        print(Err)


def catalog(tree):
    """
    需要根据不同网站进行编写 主要就是不同的xapth
    使用xpath提取html结构中的新闻页面的目录分页
    :param tree: 解析过的HTML结构
    :return: 一个URL list
    """
    title = tree.xpath(r"/html/body/div[4]/div[2]/div[3]/div/div[4]/div[2]/div/div[2]/div[2]/ul//a/text()")
    url = tree.xpath(r'/html/body/div[4]/div[2]/div[3]/div/div[4]/div[2]/div/div[2]/div[2]/ul//a/@href')
    return dict(zip(title, url))


def hot(tree):
    """
    不同网站不同写法 主要是xpath
    话题热播榜
    :param tree: 结构化过的html语句
    :return: URL地址
    """
    a_s = tree.xpath(r"/html/body/div[4]/div[2]/div[4]/div[2]/div[2]/div/div[4]/div//@href")
    for i in a_s:
        url = urllib.parse.urljoin(_URL, i)
        yield url


def recommond(tree):
    """
    不同网站不同写法 主要就是xpath路径
    tvbs的人气点击榜和编辑推荐榜
    :param tree:
    :return:
    """
    urls = tree.xpath(r'//div[@class="sidebar_div margin_b20 float-top-box"]//div[@class="list_text"]/a/@href')
    for i in urls:
        url = urllib.parse.urljoin(_URL, i)
        yield url


def now_news(tree):
    """
    tvbs的实时新闻 不同网址不同的写法
    :param tree:
    :return:
    """
    try:
        urls = tree.xpath(r'//div[@class="content_center_box background-color1 display_block_pc"]//ul/li/a/@href')
        for url in urls:
            url = urllib.parse.urljoin(_URL, url)
            yield url
    except Exception as ERR:
        print(ERR)


def news_content(url):
    """
    新闻详情页面的提前逻辑，根据不同的网站进行编写，主要就是xpath路径
    新闻信息的详情页面抓取逻辑，每次抓取新的页面就直接在这里编写xpath语句
    :param url:
    :return:
    """
    print(url)
    response = requests.get(url, headers=HEADERS)
    tree = etree.HTML(response.content.decode('utf-8'))
    # 新闻文本主题div标签 xpath路径
    cotent_xpath = tree.xpath(r'//div[@class="newsdetail_content"]')[0]
    # 图片xpath
    image = cotent_xpath.xpath(r'.//div[@class="contxt margin_b20"]/div//img/@src')
    image_info = cotent_xpath.xpath(r'.//div[@class="contxt margin_b20"]/div//img/@alt')
    # 文本xpath,去取文本的空白格
    texts = cotent_xpath.xpath(r'.//div[@id="news_detail_div"]/child::*')
    contents =[]
    for text in texts:
        p = etree.tostring(text, encoding="utf-8", pretty_print=True, method="html").decode('utf-8')
        contents.append(p)
    content = ''.join(''.join(contents).split())
    # 时间 转换为时间戳
    times = cotent_xpath.xpath(r'.//div[@class="title margin_b20"]//div[@class="icon_time time leftBox2"]/text()')[0]
    # 作者
    author = cotent_xpath.xpath(r'.//div[@class="title margin_b20"]//h4/a/text()')
    # 标题
    title = cotent_xpath.xpath(r'.//div[@class="title margin_b20"]//h1[@class="margin_b20"]/text()')[0].strip()

    return content, str(times), author, title, (image, image_info,)


def image_encode(image_url):
    """
    将image转回为base64
    :param image_url: 图片url地址
    :return: base64和url地址的元组包
    """
    try:
        response = requests.get(url=image_url, headers=HEADERS)
        Image.open(BytesIO(response.content))
        image_64 = base64.b64encode(BytesIO(response.content).read())
        image_info_pack = (image_64, image_url,)
        return image_info_pack

    except Exception as E:
        image_encode(image_url)
        print('出错了' + str(E))


def time_convert(times):
    """
    将2019/11/12等时间转换为毫秒级的时间戳
    :param times: 字体格式的时间戳
    :return: 毫秒级别的时间戳
    """
    a = time.strptime(times, '%Y/%m/%d %H:%M')
    stime = int(time.mktime(a))
    micrtime = int(stime * 1000)
    return micrtime


def url_fingerprint(url):
    """
    将url加密方便进行去重
    :param url: url
    :return: md5加密的字符串
    """
    md5_obj = hashlib.md5()
    md5_obj.update(url.encode(encoding='utf-8'))
    md5_url = md5_obj.hexdigest()
    return md5_url

def redis_ctf(url):
    """
    加密后的url添加到redis中，成功返回一个url不成功就返回一个0
    :param url:
    :return:
    """
    pool = redis.ConnectionPool(host='localhost', port=6379, max_connections=10)
    conn = redis.Redis(connection_pool=pool)
    if conn.sadd('tvbs', url):
        print(url)
        conn.save()
        return 1
    else:
        return 0

def image_file(image,):
    """
    包装image程file形态
    :param image:
    :return:
    """
    image_url, info = image
    files = []
    encode_urls = []

    if not image_url:
        return "空的"
    # else:
    #     # 给图片加密
    #     for url in image_url:
    #         encode_urls.extend(image_encode(url))

    # 更改一下调用start()
    while image_url and info:
        # 应该传入加密和 原来的url
        file = {'type': 'photo', 'url': up_load(image_encode(image_url.pop())), "info": info.pop()}
        files.append(file)

    return files


def author_packet(author):
    """
    将作者打包成上传需要的函数，
    :param author:
    :return:
    """
    if author:
        author, *_ = author
    else:
        author = None
    return {"作者": author}


def up_load(image_pack):
    """
    上传url得到服务器url地址以便传入image——flie中
    :param image_pack:一个元组内含有一个url加密过的md5字符串，一个url
    :return:返回一个start函数返回的一个url。用来构建image_file中的函数中字典中的url
    """
    # 解包得到得到base64字符串，和url
    try:
        image_banse64, image_url, *_ = image_pack
        # 调用start()函数得到返回的url
        url_packe = start(image_banse64, image_url)
        return url_packe
    except Exception as ERR:
        print(ERR)
        print(image_pack)




def hot_main():
    pass


def recomnd_main():
    assert requests.get(_URL).status_code == 200,  "连接不上"
    source = page_sourse(_URL)
    recommend_urls = recommond(source)
    for url in recommend_urls:
        comeurl = url
        # encode = url_fingerprint(url)
        # if redis_ctf(encode):
        info = news_content(url)
        _text, _times, _author, title, _image = info
        other_info = author_packet(_author)
        yuantime = time_convert(_times)
        file = image_file(_image)
        content = _text
        yield comeurl, title, other_info, yuantime, file, content
        # else:
        #     print('出错了')

def now_news_main():
    """
    主爬取程序逻辑：先爬取url随后for 对url进行加密随后放入redis集合，如果放不进去则这个url有错误那么就停止抓取
    :return:
    """
    # 断言 如果连接不上接下来就不运行了。
    assert requests.get(_URL).status_code == 200,  "连接不上"

    # try:
    # 调用page_sourse()函数获取tree格式
    source = page_sourse(_URL)
    # 调用now_news()目前获取的是主页的url 现在需要细化进行爬取各个分目录的网址
    urls = catalog(source).values()
    for url in urls:
        now_urls = now_news(page_sourse(url))
        # 遍历url
        for url in now_urls:
            # 将当前url赋给comeurl
            comeurl = url
            # 对 url加密
            encode = url_fingerprint(url)
            # 将加密的URl加入集合中，如果集合加入成功就表明这是第一次抓取该网页，如果失败则表明url有重复，
            if redis_ctf(encode):

                try:
                    info = news_content(url)
                    _text, _times, _author, title, _image = info
                    other_info = author_packet(_author)
                    yuantime = time_convert(_times)
                    file = image_file(_image)
                    content = _text
                    yield comeurl, title, other_info, yuantime, file, content

                except Exception as Err:

                    print(Err)
                    print(url)

            else:

                print('url已经存在')
            # except Exception as Err:
            # print(Err)



if __name__ == "__main__":
    while True:
        infos = now_news_main()
        for i in infos:
            comeurl, title, other_info, yuantime, file, content = i
            post_news(
                title=title, content=str(content), otherInfo=other_info,
                files=file, comeurl=comeurl, webhost=_HOST,
                yuantime=yuantime, downworkid='b67f894d-112e-4fac-966d-26c6da04942f', webname=__WEBNAME
            )
        time.sleep(240)

    # d = image_encode('https://cc.tvbs.com.tw/img/upload/2019/10/27/20191027132932-f9b71a06.jpg')
    # print(d)



    #  测试用
    # a = news_content('https://news.tvbs.com.tw/travel/1225899')
    # content, times, author, title, image = a
    # other_info = author_packet(author)
    # yuantime = time_convert(times)
    # file = image_file(image)
    # print(title)
    # print(content)
    # print(type(other_info))
    # print(type(file))
    # print(type(yuantime))
    #
    #
    # post_news(title=title, content='', otherInfo=other_info,
    #             files=file, comeurl='https://news.tvbs.com.tw/travel/1225899', webhost=_HOST,
    #             yuantime=yuantime, downworkid='b67f894d-112e-4fac-966d-26c6da04942f', webname=__WEBNAME)