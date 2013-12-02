#coding:utf-8
__author__ = 'liuyix'

from logger import setup_logging

logger = setup_logging(console=True, logfile='locate_src.log', filelog=True)


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


def usage():
    help_message = 'locate_src.py 修改后的trace文件 filtered_file result_file'
    print help_message


if __name__ == "__main__":
    # TODO 使用argparse
    import sys
    import os

    if len(sys.argv) == 4:
        assert os.path.isfile(sys.argv[1]) \
                   and os.path.isfile(sys.argv[2]) \
            and os.path.exists(os.path.dirname(sys.argv[3]))
        find_src(*sys.argv[1:])
    else:
        usage()
        sys.exit(0)
