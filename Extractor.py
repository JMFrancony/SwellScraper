# !/usr/bin/env python
# -*- coding: utf-8 -*-

''' Content parsing from ziped Web Page
'''
from CfgReader import CfgFileParser
from FileLogger import FileLogger

from Parser import ThesesParser

import time
import datetime
import sys
import os
import yapdi
import re

import json

cfg_file = 'WebPageCollector.cfg'



COMMAND_START = 'start'
COMMAND_STOP = 'stop'
COMMAND_RESTART = 'restart'

# ======================================================================================================
class Extractor(yapdi.Daemon):

    def __init__(self):
        self.file_logger = FileLogger()
        cfg_parser = CfgFileParser()
        self.Config = cfg_parser.file_reader(cfg_file)
        pid_file = self.Config['Extractor']['pid']
        self.Wait = int(self.Config['Extractor']['wait'])
        self.file_logger = FileLogger()
        self.Project = self.Config['Extractor']['project']
        Parser = self.Config[self.Project]['parser']
        self.Parser = eval(Parser + '()')
        self.Parser.Project = self.Project
        self.Parser.init_DataBase()
        try:
            Restriction = self.Config['Extractor']['restriction']
            self.Restriction = json.loads(Restriction)
            self.file_logger.csv_log('EXTRACTOR', 'Extractor init ok')
        except Exception as exp:
            self.file_logger.csv_log('ERROR',exp)
            raise
        yapdi.Daemon.__init__(self, pid_file)


    def Extracting(self):
        self.file_logger.csv_log('EXTRACTOR', 'start Extracting')

        while True:
            try:
                self.Parser.parse(self.Restriction)
                time.sleep(self.Wait)
            except Exception as exp:
                self.file_logger.csv_log('EXTRACTOR', 'Bug in Extracting():', exp)

# ============================================================================================================
LCom = [COMMAND_START, COMMAND_STOP, COMMAND_RESTART]
if len(sys.argv) < 2 or sys.argv[1] not in LCom:
    print("Bad USAGE: python %s" % sys.argv[0])
    exit()

# START
if sys.argv[1] == COMMAND_START:
    DExtractor = Extractor()
    print('start Extracting')
    if DExtractor.status():
        print("An Extracting instance is already running.")
        exit()
    retcode = DExtractor.daemonize()
    if retcode == yapdi.OPERATION_SUCCESSFUL:
        DExtractor.Extracting()
    else:
        print('Daemonization failed')

# STOP
elif sys.argv[1] == COMMAND_STOP:
    print('stop Extracting')
    DExtractor = Extractor()
    if not DExtractor.status():
        print("No Extracting instance running.")
        exit()
    retcode = DExtractor.kill()
    if retcode == yapdi.OPERATION_FAILED:
        print('Trying to stop running instance failed')

# RESTART
elif sys.argv[1] == COMMAND_RESTART:
    print('restart')
    DExtractor = Extractor()
    if DExtractor.status():
        print("An instance is already running.")
        exit()
    retcode = DExtractor.restart()
    if retcode == yapdi.OPERATION_SUCCESSFUL:
        DExtractor.Extracting()
    else:
        print('Daemonization failed')

# ============================================================================================================
if __name__ == '__main__':
    pass
