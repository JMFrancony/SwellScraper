# !/usr/bin/env python
# -*- coding: utf-8 -*-

''' dedicated spiders Python 3
'''


import scrapy
from CfgReader import CfgFileParser
from FileLogger import FileLogger
from selenium.common.exceptions import NoSuchElementException
from scrapy.utils.response import open_in_browser
from scrapy.contrib.spiders import Rule
from scrapy.linkextractors import LinkExtractor
# from selenium import webdriver
import json
import time
import datetime
import random
import lxml.etree as ETree
from twisted.internet import reactor, defer

CONFIGFILE= 'WebPageCollector.cfg'

#======================================================================================================
class DOM(scrapy.Item):
    # Defines an item to contain the scraped HTML DOM
    dom_tree = scrapy.Field()
    profile_url = scrapy.Field()
    page_url = scrapy.Field()
    level = scrapy.Field()
    

# ======================================================================================================
class ThesesSpider(scrapy.Spider):
    # Defines a spider dedicated to crawling Theses.fr
    # works on URL like : http://www.theses.fr/<IDTHESE>
    name = 'PhD'
    allowed_domains = ["Theses.fr"]
    # rules = (Rule(LinkExtractor(allow=(), restrict_xpaths=('//li[@class="pager-next"]',)), callback="parse", follow=True),)

    def __init__(self, profile_url='',next=False, *args, **kwargs):
        # Get value for given attributes
        super(ThesesSpider, self).__init__(*args, **kwargs)
        self.start_urls = [profile_url]
        self.Next = next
        # Instantiate a FileLogger object
        self.file_logger = FileLogger()

    def parse(self, response):
        # Get the page's body HTML
        self.file_logger.csv_log('SPIDER', 'path', '')
        html_dom = response.xpath('//body').extract()
        # Write the HTML DOM into the dom_tree field of a DOM item
        dom = DOM(dom_tree=html_dom,
                    profile_url=self.start_urls[0],
                    page_url=response.url,
                    level=1)
        self.file_logger.csv_log('SPIDER', 'Success', response.url)
        yield dom

    def errback(self, failure):
        # In case of error, log the error's message
        self.file_logger.csv_log('SPIDER', repr(failure), self.start_urls[0])