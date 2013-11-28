# coding=utf-8
__author__ = 'liuyix'

import logging


def calculate_online(filename, outpath, dupfile=None):
    assert os.path.isfile(filename)

    # 用addr_map确保所有distinct_addr_sequence都对应唯一的addr
    addr_map = {}
    distinct_addr_idx_sequence = []

    #reuse_distance_buffer = []
    output_fileobj = open(outpath, 'w')
    if dupfile is None:
        duplicate_trace = open(filename + '.mod.trace', 'w')
    else:
        duplicate_trace = open(dupfile)

    with open(filename) as trace_fileobj:
        valid_info = {'src': 'unknown', 'linum': '-1', 'col': '-1'}
        for idx, line in enumerate(trace_fileobj):
            # TODO: 格式相关！！！
            line_infos = line.split(':')
            if line_infos[-1].strip() != 'unknown':
                #logging.debug('found: %s', line_infos[-1])
                valid_info['src'] = line_infos[-1]
                valid_info['linum'] = line_infos[-2]
                valid_info['col'] = line_infos[-3]
            else:
                line_infos[-1] = valid_info['src']
                line_infos[-2] = valid_info['linum']
                line_infos[-3] = valid_info['col']
            duplicate_trace.write(' : '.join(line_infos) + '\n')

            laddr = line_infos[0]
            if laddr not in addr_map:
                #addr_map[laddr] = (idx, valid_info['src'], valid_info['linum'])
                addr_map[laddr] = idx
                distinct_addr_idx_sequence.append(idx)
                # -1表示负无穷
                reuse_distance = -1
            else:
                #当前addr出现过，那么计算上一次addr出现的位置到最后的距离即可
                old_idx = addr_map[laddr]
                last_distinct_location = distinct_addr_idx_sequence.index(old_idx)
                reuse_distance = len(distinct_addr_idx_sequence) - last_distinct_location - 1
                distinct_addr_idx_sequence.remove(old_idx)
                distinct_addr_idx_sequence.append(idx)
                addr_map[laddr] = idx

            #if reuse_distance < sys.maxint:
            #    # 不记录第一次出现的addr
            #    output_fileobj.write("%d\n" % reuse_distance)
            output_fileobj.write("%d\n" % reuse_distance)
    output_fileobj.close()
    duplicate_trace.close()


if __name__ == "__main__":
    import sys
    import os

    logging.basicConfig(level=logging.DEBUG)
    if len(sys.argv) < 3:
        print("必须指定trace文件路径和输出结果路径!")
        sys.exit(0)
    if not os.path.isfile(sys.argv[1]) or not os.path.isdir(os.path.dirname(sys.argv[2])):
        print("%s: no such file or directory", sys.argv)
        sys.exit(0)
    print("Trace: %s\nResult:%s\n" % (sys.argv[1], sys.argv[2]))
    calculate_online(sys.argv[1], sys.argv[2])
    pass