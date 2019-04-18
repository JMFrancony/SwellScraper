# !/usr/bin/env python
# -*- coding: utf-8 -*-

''' a Pipeline for data output.
'''

from FileLogger import FileLogger
from scrapy import signals
from twisted.internet import reactor
from scrapy.exporters import JsonLinesItemExporter
from DataCompressor import BinaryCompressor
import pymongo
from pymongo import  MongoClient
from pymongo.errors  import ConnectionFailure
from CfgReader import CfgFileParser
import datetime
import json
import codecs


CONFIGFILE= 'WebPageCollector.cfg'
#============================================================================================================
class JSONPipeline(object):
    # Defines a class to save the scraped data into a json line file
    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)

        return pipeline

    def spider_opened(self,spider):
        # Open the file and start to export data
        self.file_logger = FileLogger()
        self.file_logger.csv_log('PIPELINE', 'open a JSON pipeline')
        self.file = codecs.open('output.json', 'wb','utf-8')
        self.exporter = JsonLinesItemExporter(self.file)
        self.exporter.start_exporting()

    def spider_closed(self,spider):
        # Stop exporting data and close the file
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self,item,spider):
        # Export the data scraped by the spider
        self.exporter.export_item(item)
        return item

#============================================================================================================
class MongoPipeline(object):
    # Defines a class to save the scraped data into MongoDB
    
    def spider_opened(self,spider):
        # Get the database parameters from the .cfg file
        cfg_parser = CfgFileParser()
        self.Config = cfg_parser.file_reader(CONFIGFILE)
        # Assign the mongoDB information
        self.file_logger = FileLogger()
        self.Project = self.Config['Collector']['project']
        self.mongo_db = self.Config[self.Project]['mongo_db']
        self.Host = self.Config[self.Project]['host']
        self.Port = int(self.Config[self.Project]['port'])
        self.Collection = self.Config[self.Project]['collection']
        self.DataSet = self.Config[self.Project]['dataset']
        self.mongo_client = MongoClient(self.Host, self.Port)
        self.DBase = self.mongo_client[self.mongo_db]
        self.DBase[self.Collection].ensure_index([('idx', pymongo.ASCENDING),('created_at', pymongo.ASCENDING)])
        self.Idx = 0
        Cursor = self.DBase[self.Collection].find({}).sort([('created_at',pymongo.DESCENDING)]).limit(1)
        for Record in Cursor :
            self.Idx = Record['idx']
        self.file_logger = FileLogger()
        self.file_logger.csv_log('PIPELINE', 'open a MONGO pipeline')
    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
#         crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def spider_closed(self,spider):
        self.mongo_client.close()

    def process_item(self, item, spider):
        # Export the data scraped by the spider
        # Get the dom as a str from the scrapy.Item
        dom_list = item['dom_tree']
        item_comp = BinaryCompressor.compress(dom_list[0])
        self.Idx +=1
        self.file_logger.csv_log('INFO', 'process_item', self.Idx)
        Record = {'created_at': datetime.datetime.now(),
                         'parsed': False,
                        'profile_url': item['profile_url'],
                        'page_url': item['page_url'],
                        'level': item['level'],
                        'zipdom': item_comp,
                        'dataset':self.DataSet,
                        'idx':self.Idx}
        self.DBase[self.Collection].insert(Record)
        return item

