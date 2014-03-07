# coding=utf-8
__author__ = 'liuyix'

import logging

# 读取trace文件，计算对应的reuse distance序列#
# *注意*，当输入trace不同时，需要修改get_vaddr方法

def get_vaddr(line):
    """*注意*该方法与trace文件格式相关，可能需要修改！
    Input: trace中的一行
    Output: 访存的虚存地址
    """
    assert isinstance(line, str)
    line_infos = [l.strip() for l in line.split(' : ')]
    return line_infos[0]


def calculate_online(filename, outpath, dupfile=None, mark_location=False):
    """
    dupfile和mark_location用于实现标记trace中每个访存地址对应的程序代码位置
    使用的前提条件是生成如下的trace文件格式：
    vaddr : pc : R/W : src_col : src_linum : src
    e.g.
    168d014 : 0x400694 : R : 0 : 28 : /home/liuyix/Dev/loop_benchmark/loop_benchmark.c
    或者当src不可知时（系统调用等）
    7fca89437e88 : 0x7fca890b1000 : R : 0 : 0 : unknown
    """
    assert os.path.isfile(filename)

    # 用addr_map确保所有distinct_addr_sequence都对应唯一的addr
    addr_map = {}
    distinct_addr_idx_sequence = []

    output_fileobj = open(outpath, 'w')
    duplicate_trace = None
    if mark_location:
        if dupfile is None:
            duplicate_trace = open(filename + '.mod.trace', 'w')
        else:
            duplicate_trace = open(dupfile, 'w')

    with open(filename) as trace_fileobj:
        valid_info = {'src': 'unknown', 'linum': '-1', 'col': '-1'}
        for idx, line in enumerate(trace_fileobj):
            # TODO: 此处解析每一行的trace
            if mark_location and duplicate_trace is not None:
                line_infos = [l.strip() for l in line.split(' : ')]
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

            laddr = get_vaddr(line)
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
    if duplicate_trace is not None:
        duplicate_trace.close()


if __name__ == "__main__":
    import sys
    import os

    logging.basicConfig(level=logging.DEBUG)
    if len(sys.argv) < 3:
        print("必须指定trace文件路径和输出结果路径!")
        print("parameter#1: trace-file\nparameter#2: output-file")
        sys.exit(0)
    print("Trace: %s\nResult:%s\n" % (sys.argv[1], sys.argv[2]))
    calculate_online(sys.argv[1], sys.argv[2])
    pass