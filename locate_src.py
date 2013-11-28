#coding:utf-8
__author__ = 'liuyix'

import logging

logger = None


def setup_logging(console=True, filelog=True):
    l_logger = logging.getLogger('locate_src')
    l_logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(funcName)s - %(levelname)s - %(lineno)d - %(message)s')
    if filelog:
        file_handler = logging.FileHandler('locate_src.log')
        file_handler.setFormatter(formatter)
        l_logger.addHandler(file_handler)
    if console:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        l_logger.addHandler(stream_handler)
    return l_logger


def find_src(trace_name, filter_name, result_file):
    import linecache

    with open(filter_name) as filter:
        with open(result_file, 'w') as result:
            last_src_info = []
            for line in filter:
                if line.isspace():
                    continue
                if not line.split()[0].strip().isdigit():
                    result.write(line)
                else:
                    src_info = linecache.getline(trace_name, int(line.split()[-1])).split(' : ')[-3:]
                    if src_info != last_src_info:
                        last_src_info = src_info
                        result.write(line.rstrip() + ' ' + ' '.join(src_info))
                    else:
                        result.write(line)
    pass


def usage():
    help_message = 'locate_src.py 修改后的trace文件 filtered_file result_file'
    print help_message


if __name__ == "__main__":
    # TODO 使用argparse
    import sys

    logger = setup_logging()

    if len(sys.argv) == 4:
        find_src(*sys.argv[1:])
    else:
        usage()
        sys.exit(0)
