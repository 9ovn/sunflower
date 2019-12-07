import requests
from lxml import etree
import arrow
from PIL import Image
from io import BytesIO
import base64
import hashlib
from forlost_sdk import *
import redis
from pymysql import connect
import random
from fake_useragent import UserAgent
from dateutil import parser

__all__ = ['ProcessTool', 'RedisCertified']




class ProcessTool:

    def __repr__(self):
        return "上传处理工具"

    def __str__(self):
        return '本类主要应用于抓取结束过后的处理过程'

    def __init__(self):
        pass

    def __headers(self):
        """
        这里只添加了ua头后续不同网站有需求就在这里修改
        :return:
        """
        headers = {
            "User-Agent": UserAgent().random,
            'Connection': 'close'
        }
        return headers

    def pageSourse(self, url):
        """
        解析指定url
        :param url: 需要爬取的url地址
        :return: 返回一个解析过的HTML结构
        """
        import urllib3.contrib.pyopenssl
        urllib3.contrib.pyopenssl.inject_into_urllib3()
        i = 0
        while i<3:
            try:
                response = requests.get(url=url, headers=self.__headers(), timeout=21)
                requests.adapters.DEFAULT_RETRIES = 5
                tree = etree.HTML(response.content.decode('utf-8'))
                return tree
            except Exception as Err:
                print(Err)
                time.sleep(60)
                print(url)
                i+=1


    def timeConvert(self, times):
        """
        将2019/11/12等时间转换为毫秒级的时间戳
        :param times: 字体格式的时间戳
        :return: 毫秒级别的时间戳
        """
        dtime = parser.parse(times)
        micrtime = int(arrow.get(dtime).timestamp * 1000)
        return micrtime


    def imageEncode(self, image_url):
        """
        接受一个图片url，将图片保存到内存之后转成base64形式的
        :param image_url: 图片url地址
        :return: base64和url地址的元组包
        """
        try:
            response = requests.get(url=image_url, headers=self.__headers())

            if str(response.status_code).startswith('2'):
                try:
                    Image.open(BytesIO(response.content))
                    image_64 = base64.b64encode(BytesIO(response.content).read())
                    image_info_pack = (image_64, image_url,)
                    print(image_64)
                    return image_info_pack
                except Exception as Err:
                    print(Err)

            else:
                print('连接出错')
        except:
            return None


    def upLoad(self, image_pack):
        """
        上传url得到服务器url地址以便传入image——flie中
        :param image_pack:一个元组内含有一个url加密过的md5字符串，一个url
        :return:返回一个start函数返回的一个url。用来构建image_file中的函数中字典中的url
        """
        # 解包得到得到base64字符串，和url
        try:
            if image_pack:
                image_banse64, image_url, *_ = image_pack
            else:
                return None

        except Exception as E:
            print('解包出错' + str(E))
        # 调用start()函数得到返回的url
        try:
            url_packe = start(image_banse64, image_url)
        except Exception as Err:
            print('start函数调用出错' + str(Err))
        return url_packe

    def imageFile(self, image,):
        """
        包装image程file形态
        :param image:
        :return:
        """
        try:
            image_url, info = image
            image_num, info_num =len(image_url), len(info)
            print(image_num)
            print(info_num)
            files = []
        except:
            return  [{'type': 'photo', 'url': None, "info": None}]

        if not image_num:
            return [{'type': 'photo', 'url': None, "info": None}]

        elif not info_num:
            try:
                while image_url:
                    file = {'type': 'photo', 'url': self.upLoad(self.imageEncode(image_url.pop())), "info":None}
                    files.append(file)
                return files
            except Exception as Err:
                print('imageFile函数中嵌套的upLoad和imageEncode函数出错' + str(Err))

        elif (info_num < image_num) or (info_num > image_num):
            try:
                while image_url:
                    file = {'type': 'photo', 'url': self.upLoad(self.imageEncode(image_url.pop())), "info": info[0]}
                    files.append(file)
                    print('f2')
                return files
            except Exception as Err:
                print('imageFile函数中嵌套的upLoad和imageEncode函数出错' + str(Err))

        elif image_num == info_num:
            # 更改一下调用start()
            try:
                while image_url and info:
                    # 应该传入加密和 原来的url
                    file = {'type': 'photo', 'url': self.upLoad(self.imageEncode(image_url.pop())), "info": info.pop()}
                    files.append(file)
                    print('f3')
                return files
            except Exception as Err:
                print('imageFile函数中嵌套的upLoad和imageEncode函数出错' + str(Err))


    def authorPacket(self, author):
        """
        将作者打包成上传需要的函数，
        :param author:list
        :return:
        """
        if author:
            author, *_ = author
        else:
            author = None
        return {"作者": author}





class RedisCertified:
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            if not hasattr(cls, 'pool'):
                cls.pool = RedisCertified.__redisConnect()
                cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self):
        return "url验证工具&数据储存（有必要的情况下）"

    def __str__(self):
        return '本类用于将加密url加入redis中实现去重以及url持久化'

    def __init__(self, name):
        self.conn = redis.Redis(connection_pool=RedisCertified.pool)
        self.name = name  # 这个地方填写你爬取网站的名字最后英文缩写

    @staticmethod
    def __redisConnect():
        """
        配合new
        :return:
        """
        return redis.ConnectionPool(host='localhost', port=6379)

    @staticmethod
    def urlFingerPrint(url):
        """
        将url加密方便进行去重
        :param url: url
        :return: md5加密的字符串
        """
        md5_obj = hashlib.md5()
        md5_obj.update(url.encode(encoding='utf-8'))
        md5_url = md5_obj.hexdigest()
        return md5_url

    def urlAdd(self, url):
        """
        判断url是否爬取过,返回 true 和 false做判断用。
        :param url: 加密后的url
        :return:
        """
        if self.conn.sadd(self.name, url):
            # 不太确定加不加这个应为会堵塞redis
            self.conn.save()
            return True
        else:
            return False


if __name__ == "__main__":
    a = RedisCertified('acdc')
    a2 = RedisCertified('acdc')
    fp = a.urlFingerPrint("https://www.runoob.com/python/python-exceptions.html")
    print(fp)
    # print(id(a))
    # print(id(a2))