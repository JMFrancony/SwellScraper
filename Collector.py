# !/usr/bin/env python
# -*- coding: utf-8 -*-

''' a sheduled WebPageCollector Python 3
'''

from Agenda import Agenda, DailyAgenda, WeeklyAgenda
from URLRoller import URLRoller
from Spiders import ThesesSpider
from CfgReader import CfgFileParser
from FileLogger import FileLogger
import pymongo
from pymongo import  MongoClient
from pymongo.errors  import ConnectionFailure
from twisted.internet import reactor, defer
import scrapy
from scrapy.crawler import CrawlerRunner,Crawler

import datetime 
import time
import json


CONFIGFILE= 'WebPageCollector.cfg'

#============================================================================================================
class WebPageCollector():

    def __init__(self):
        cfg_parser = CfgFileParser()
        self.Config = cfg_parser.file_reader(CONFIGFILE)
        self.Project = self.Config['Collector']['project']
        self.Drop = self.Config[self.Project]['drop'] == 'True'
        self.Cycle = self.Config[self.Project]['cycle'] == 'True'
        self.Next = self.Config[self.Project]['next'] == 'True'
        self.mongo_db = self.Config[self.Project]['mongo_db']
        self.Host = self.Config[self.Project]['host']
        self.Port = int(self.Config[self.Project]['port'])
        self.Collection = self.Config[self.Project]['collection']
        self.mongo_client = MongoClient(self.Host, self.Port)
        self.DBase = self.mongo_client[self.mongo_db]
        if self.Drop :
            self.DBase[self.Collection].drop()
        self.file_logger = FileLogger()
        self.set_up()

    def set_up(self):
        PipeLines = self.Config[self.Project]['pipelines']
        PipeLines = json.loads(PipeLines)
        self.spider_settings = {
                            'USER_AGENT': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36 OPR/38.0.2220.41',
                            'DOWNLOADER_MIDDLEWARES ': {'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': 543},
                            'DOWNLOAD_DELAY': 3,
                            'RANDOMIZE_DOWNLOAD_DELAY': True,
                            'COOKIES_DEBUG': False,
                            'COOKIES_ENABLED': True,
                            'ITEM_PIPELINES': PipeLines,
                            'LOG_LEVEL' : 'INFO'
                         }
        self.SpiderName = self.Config[self.Project]['spider']
        self.URLRoller = URLRoller()
        if self.Config['Agenda']['pace'] == 'daily':
            self.Agenda = DailyAgenda()
        if self.Config['Agenda']['pace'] == 'weekly':
            self.Agenda = WeeklyAgenda()
        self.file_logger.csv_log('COLLECTOR', 'SetUp is done')


    def Crawl_job(self,URL,Next):
        Runner = CrawlerRunner(settings=self.spider_settings)
        return Runner.crawl(eval(self.SpiderName),profile_url=URL,next=Next)

    def Schedule_next_crawl(self,null,Now):
        self.file_logger.csv_log('COLLECTOR', 'Crawl Session will start')
        if self.Agenda.Begin <= Now and Now < self.Agenda.End :
            delay = self.Agenda.Delay(Now)
            self.file_logger.csv_log('COLLECTOR', 'delayed by',delay)
            reactor.callLater(delay,self.LoopCapturing)
        else:
            self.file_logger.csv_log('COLLECTOR', 'Crawl Session is ended')
            reactor.stop()

    def Capturing(self):
        Now = datetime.datetime.now()
        URL = self.URLRoller.next()
        print(Now.time(),'->',URL)
        Job = self.Crawl_job(URL,self.Next)
        Job.addCallback(self.Schedule_next_crawl,Now)
        Job.addErrback(self.errback)

    def CaptureOnes(self,URL):
        print('->',URL)
        Now = datetime.datetime.now()
        Job = self.Crawl_job(URL,False)
        Job.addCallback(self.Schedule_next_crawl,Now)
        Job.addErrback(self.errback)

    def LoopCapturing(self):
        Now = datetime.datetime.now()
        URL = self.URLRoller.next()
        if URL == self.URLRoller.starter() and not self.Cycle :
            reactor.stop()
        else:
            print(Now.time(),'->',URL)
            Job = self.Crawl_job(URL,self.Next)
            Job.addCallback(self.Schedule_next_crawl,Now)
            Job.addErrback(self.errback)


    def errback(self,failure):
        print('ERROR:',failure.value)
        self.file_logger.csv_log('COLLECTOR', failure.value, self.start_urls[0])

#============================================================================================================
if __name__ == '__main__':
    WPC = WebPageCollector()
    WPC.Capturing()
    reactor.run()
