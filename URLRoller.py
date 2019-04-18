# !/usr/bin/env python
# -*- coding: utf-8 -*-

''' used for URL list exploration Python 3
'''

import itertools
import re
import codecs

from CfgReader import CfgFileParser
from FileLogger import FileLogger

CONFIGFILE = 'WebPageCollector.cfg'

# ============================================================================================================
class URLRoller():

    def __init__(self):
        self.file_logger = FileLogger()
        cfg_parser = CfgFileParser()
        self.Config = cfg_parser.file_reader(CONFIGFILE)
        self.Project = self.Config['Collector']['project']
        self.step = int(self.Config[self.Project]['loader'])
        enum_list = []
        for Idx in range(self.step):
            print('in the loop')
            col_data = self.Config[self.Project ][str(Idx+1)]
            file_in = codecs.open(col_data, 'r', 'utf-8')
            Cpt = 0
            for Line in file_in:
                URL = Line[:-1].strip()
                URL = re.sub(r'\s+', ' ', URL)
                enum_list.append(URL)
                Cpt +=1
                self.file_logger.csv_log('URL %s:' % Cpt, URL)
        self.URLList = enum_list
        self.StartURL = enum_list[0]
        self.URLRoller = itertools.cycle(enum_list)

    def next(self):
        return next(self.URLRoller)
    
    def starter(self):
        return self.StartURL

# ============================================================================================================
if __name__ == '__main__':
    URLRoller = URLRoller()
    for i in range(10):
        print(i, URLRoller.next())