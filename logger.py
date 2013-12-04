#coding: utf-8
__author__ = 'liuyix'

import logging


def setup_logging(console=True, logfile='foo.log', filelog=True):
    assert isinstance(console, bool) and isinstance(filelog, bool) and isinstance(logfile, str)
    l_logger = logging.getLogger('locate_src')
    l_logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(funcName)s - %(lineno)d - %(levelname)s - %(message)s')
    if filelog:
        file_handler = logging.FileHandler(logfile)
        file_handler.setFormatter(formatter)
        l_logger.addHandler(file_handler)
    if console:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        l_logger.addHandler(stream_handler)
    return l_logger