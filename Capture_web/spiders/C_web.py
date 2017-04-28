# -*- coding:utf-8 -*-
import scrapy
import json
import sys
import time
import urlparse
from urllib2 import urlopen
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from cStringIO import StringIO
reload(sys)
sys.setdefaultencoding('utf8')

from Capture_web.items import CaptureWebItem

class C_web(scrapy.spiders.Spider):
    name = "captureweb"
    allow = ["cqgs12315.cn","cqgs.gov.cn","miit.gov.cn","qiye.gov.cn","11467.com","sina","sohu"]
    start_urls = [
#            "http://www.eastmoney.com/",
#            "http://www.cninfo.com.cn/cninfo-new/index",
            "http://finance.sina.com.cn/",
            "http://business.sohu.com/",
#            "http://www.stats.gov.cn",
#            "http://www.cqtj.gov.cn",
            "http://www.cqgs12315.cn",
            "http://www.miit.gov.cn",
            "http://news.qiye.gov.cn",
            "http://chongqing.11467.com",
#            "http://finance.eastmoney.com/news/1345,20170424732060562.html",
#            "http://stock.eastmoney.com/news/1407,20170425732338777.html"
    ]

    linked = {}
    flag = 0
    city = ["重庆","渝中","大渡口","江北","沙坪坝","九龙坡","南岸","北碚","渝北","巴南",
            "綦江","万州","涪陵","黔江","长寿","江津","大足","合川","永川","南川"
            "潼南","铜梁","荣昌","璧山","梁平","城口","丰都","垫江","武隆","忠县","开县",
            "云阳","奉节","巫山","巫溪""石柱","秀山","酉阳","彭水"]

    keywords = ["创新","人工智能","AI","智能制造","智慧驾驶","无人驾驶","汽车智能化","新能源",
            "车联网","投资","并购","升级","改造","转型","项目","发展","战略","产业布局",
            "供给测","去库存","一带一路","新材料","大数据","云计算","物联网","机器人",
            "无人操作","OEM","绿色","生态"]

    def readPDF(self, html):
        rsrcmgr = PDFResourceManager()
        retstr = StringIO()
        codec = 'utf-8'
        laparams = LAParams()
        device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)

        fp = StringIO(html)

        interpreter = PDFPageInterpreter(rsrcmgr, device)
        pagenos=set()
        for page in PDFPage.get_pages(fp, pagenos, maxpages=0, password="",caching=True, check_extractable=True):
                interpreter.process_page(page)
        fp.close()
        device.close()

        string = retstr.getvalue()
        retstr.close()
        return string


    def judge(self, string):

        I_city = ''
        I_key = []
        for C in self.city:
            if C in string:
                I_city = C
                break
        for K in self.keywords:
            if K in string:
                I_key.append(K)
        return I_city,I_key

    #PDF 处理
    def parse_pdf(self, response):

        self.flag = self.flag + 1
        print response.url,self.flag

        f = open('result.json','a')     #获取文件句柄
        city = ''       #初始化城市
        key = []        #初始化关键字
        context = []        #初始化内容

        #处理包含PDF 的正文和链接
        if 'PDF' in response.url or 'pdf' in response.url:
            pdffile = urlopen(response.url).read()
            ots = self.readPDF(pdffile)
            context.append(ots)
        elif '.apk' in response.url:
            return
        else:
            context = response.xpath('//p').extract()
            context2 = response.xpath('//h1').extract()
            context.extend(context2)

        #判断正文是否符合要求
        for C in context:
            citys,keys = self.judge(C)
            if not len(city):
                city = citys
            if len(keys) > 0 :
                key= list(set(key)|set(keys))
        if len(city) > 0 and len(key) > 0:
            keyword = ''
            for K in key:
                keyword = keyword + K + ','
            f.write(response.url+'\t'+city+'\t'+keyword+'\n')

        f.close()

        #处理该url 包含的链接
        if 'PDF' in response.url:
            return
        link = response.xpath('//a/@href').extract()
        model = response.xpath('//iframe/@src').extract()
        link = list(set(link) | set (model))
        for L in link:
            if 'http' in L and 'stats.gov.cn' in L and 'download' not in L:
                if self.linked.get('L'):
                    continue
                self.linked.update({L:1})
                yield scrapy.http.Request(L, callback = self.parse)

    #非常规url 处理
    def parse_url(self, response):

        self.flag = self.flag + 1
        print response.url,self.flag

        f = open('result.json','a')     #获取文件句柄
        city = ''       #初始化城市
        key = []        #初始化关键字
        context = []        #初始化内容

        #处理包含PDF 的正文和链接
        if 'PDF' in response.url:
            pdffile = urlopen(response.url).read()
            ots = self.readPDF(pdffile)
            context.append(ots)
        else:
            context = response.xpath('//p').extract()
            context2 = response.xpath('//h1').extract()
            context.extend(context2)

        #判断正文是否符合要求
        for C in context:
            citys,keys = self.judge(C)
            if not len(city):
                city = citys
            if len(keys) > 0 :
                key= list(set(key)|set(keys))
        if len(city) > 0 and len(key) > 0:
            keyword = ''
            for K in key:
                keyword = keyword + K + ','
            f.write(response.url+'\t'+city+'\t'+keyword+'\n')

        f.close()

        #处理该url 包含的链接
        if 'PDF' in response.url:
            return
        link = response.xpath('//a/@href').extract()
        model = response.xpath('//iframe/@src').extract()
        link = list(set(link) | set (model))
        for L in link:
            if len(L) < 1:
                continue
            if L[0] == '/':
                L = "http://www.cninfo.com.cn" + L
            if L[0] == '.':
                L = response.url +'/'+ L
            if 'http' in L and 'cninfo.com.cn' in L and 'download' not in L\
                and '/bottomnew.htm/../bottomnew.htm/' not in L:
                if self.linked.get('L'):
                    continue
                self.linked.update({L:1})
                yield scrapy.http.Request(L, callback = self.parse)

    #通用逻辑处理
    def parse(self, response):

        f = open('result.json','a')

        city = ''
        key = []

        self.flag = self.flag + 1
        print response.url,self.flag

        context = response.xpath('//p').extract()
        context2 = response.xpath('//h1').extract()
        context.extend(context2)
        for C in context:
            citys,keys = self.judge(C)
            if not len(city):
                city = citys
            if len(keys) > 0 :
                key= list(set(key)|set(keys))
        if len(city) > 0 and len(key) > 0:
            keyword = ''
            for K in key:
                keyword = keyword + K + ','
            f.write(response.url+'\t'+city+'\t'+keyword+'\n')

        f.close()

        link = response.xpath('//a/@href').extract()
        for I in link:
	    print I
            if len(I) < 1:
                continue
            if not( I[:4] == 'http'):
                I = urlparse.urljoin(base=response.url, url=I)
	    flag = 0
	    for F in self.allow:
		if F in I:
		    flag = 1
		    break 
            if 'http' in I and flag:
                if self.linked.get('I'):
                    continue
                self.linked.update({I:1})
                time.sleep( 0.2 )
                yield scrapy.http.Request(I, callback = self.parse)

