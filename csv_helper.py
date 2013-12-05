#coding: utf-8
__author__ = 'liuyix'

import csv


class CsvHelper:
    def __init__(self, out_name, delimiter=';', quotechar='"'):
        self.file_name = out_name
        self.__fobj = open(self.file_name, 'wb')
        self.writer = csv.writer(self.__fobj, delimiter=delimiter, quotechar=quotechar, quoting=csv.QUOTE_ALL)

    def __del__(self):
        if self.__fobj is not None:
            self.__fobj.close()

    def write(self, row):
        self.writer.writerow(row)


def do_test():
    csvhelper = CsvHelper('test-csv.csv')
    csvhelper.write([str(1), "abc", str(1.0)])

if __name__ == "__main__":
    do_test()