# !/usr/bin/env python
# -*- coding: utf-8 -*-

''' used to log actions
'''

from datetime import datetime
import csv

# ============================================================================================================
class FileLogger:
    # Handles the logging of events into a file
    def __init__(self):
        self.f = None

    def txt_log(self, message):
        # Open a file object in appending mode, or create it
        self.f = open('scraping_log.txt', 'a+')
        # Writes in the file
        self.f.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ' + message + '\n')
        # Closes the file
        self.f.close()

    def csv_log(self, message, *args):
        arg_list = [datetime.now().strftime('%Y-%m-%d %H:%M:%S'), message]
        for count, arg in enumerate(args):
            arg_list.append(arg)
        with open('scraping_log.csv', "a+", newline='') as self.f:
            writer = csv.writer(self.f, delimiter=',')
            writer.writerow(arg_list)


if __name__ == '__main__':
    file_logger = FileLogger()
    file_logger.csv_log('Hola !', 552, 'Salut !', 12, 'Hi !')
