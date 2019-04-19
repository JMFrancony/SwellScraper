# !/usr/bin/env python
# -*- coding: utf8 -*-

''' For Specific Page Extraction Information Based on DB Information
'''

from FileLogger import FileLogger
from datetime import datetime, time, timedelta
from CfgReader import CfgFileParser
import os
from DataCompressor import BinaryDecompressor
import codecs
import re
from urllib.parse import urlparse

import pymongo
from pymongo import  MongoClient
from pymongo.errors  import ConnectionFailure
from bson.objectid import ObjectId
from bs4 import BeautifulSoup

cfg_file = 'WebPageCollector.cfg'

DAYHM_RGX = '(\d\d\/\d\d\/\d\d).*?(\d+h\d\d)'
DAYHM_RGX2 = '(\d\d\/\d\d\/\d\d\d\d).*?(\d\d:\d\d)'
ATTRIB_RGX = '(.+?):(.*)'

#===============================================================================================
class WebPageParser():
    # Handle the extraction process.
    def __init__(self):
        self.file_logger = FileLogger()
        cfg_parser = CfgFileParser()
        self.Config = cfg_parser.file_reader(cfg_file)
        self.Project=''

    def parse(self,Restriction={}):
        self.Parser.parse(Restriction)

    def init_DataBase(self):
        try :
            self.Host =  self.Config[self.Project]['host']
            self.Port =  int(self.Config[self.Project]['port'])
            Connector = MongoClient(host=self.Host, port = self.Port) # Client
            self.DataBase = self.Config[self.Project]['mongo_db']
            self.ColIn = self.Config[self.Project]['collection']
            self.ColOut = self.Config[self.Project]['collection_out']
            self.DBase = Connector[self.DataBase]
        except ConnectionFailure :
            self.file_logger.csv_log('ALERTE', 'DBase is down...')
            sys.exit(1)  


    def PrettifyText(self,Text,Seq=['\n+','\r+','\t+','\s+']):
        for W in Seq :
            Text= re.sub(W , ' ', Text)
        return Text.strip()

#=============================================================================================== 
class ThesesParser(WebPageParser):
    # Handle the extraction process for Theses.fr

    def __init__(self):
        super(ThesesParser, self).__init__()

    def ParseTitle(self,Content):
        Title = ''
        Value = Content.select('h1[property=dc:title]')
        if len(Value)> 0:
            Title = Value[0].get_text()
        return Title.strip()

    def ParseSummary(self,Content):
        Summary = ''
        Value = Content.select('span[property=dc:description]')
        if len(Value)>0 :
            Summary = Value[0].get_text()
        return Summary

    def ParseName(self,Content):
        Name = ''
        Value = Content.select('span[property=foaf:name]')
        if len(Value)> 0:
            Name = Value[0].get_text()
        return Name.strip()

    def ParseKeyWords(self,Content):
        KeyWords = []
        Value = Content.select('span[property=dc:subject]')
        for KeyWord in Value :
            KeyWords.append(KeyWord.get_text().strip())
        return KeyWords

    def ParseDate(self,Content):
        Date=''
        Value = Content.select('span[property=dc:date]')
        if len(Value)> 0:
            Date = Value[0].get_text()
            Date = Date.strip()[-4:]
        return Date

    def ParseWebPage(self, Record):
        Result = {}
        WebPage = BinaryDecompressor.decompress(Record['zipdom'])
        soup = BeautifulSoup(WebPage, 'html.parser')
        Title = self.ParseTitle(soup)
        Summary = self.ParseSummary(soup)
        Name = self.ParseName(soup)
        KeyWords = self.ParseKeyWords(soup)
        Date = self.ParseDate(soup)
        Result['title']= Title
        Result['summary']= Summary
        Result['keywords'] = KeyWords[1:]
        Result['discipline']= KeyWords[0]
        Result['name'] = Name
        Result['date'] = Date
        return Result


    def parse(self, Restriction={}):
        self.DBase[self.ColOut].drop()
        self.DBase[self.ColOut].ensure_index([('phid', pymongo.ASCENDING), ('dataset', pymongo.ASCENDING)],
                                             unique=True)
        Cursor = self.DBase[self.ColIn].find(Restriction)
        print(Cursor.count(), 'element(s) are found for', self.Project)
        for Record in Cursor:
            Result = self.ParseWebPage(Record)
            Result['dataset']= Record['dataset']
            Result['idx']= Record['idx']
            URL = Record['page_url']
            Result['phid']=URL.split('/')[-1].strip()
            self.DBase[self.ColOut].insert(Result)

#===============================================================================================
if __name__ == '__main__':
    TH = ThesesParser()
    TH.Project = 'Theses'
    TH.init_DataBase()
    TH.parse()
