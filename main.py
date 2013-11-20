# coding=utf-8
__author__ = 'liuyix'


def do_main(filepath, outpath):
    calculate_online(filepath, outpath)


def calculate_online(filename, outpath):
    assert os.path.isfile(filename)

    # 用addr_map确保所有distinct_addr_sequence都对应唯一的addr
    addr_map = {}
    distinct_addr_idx_sequence = []

    #reuse_distance_buffer = []
    output_fileobj = open(outpath, 'w')

    with open(filename) as trace_fileobj:
        for idx, line in enumerate(trace_fileobj):
            laddr = line.split(':')[0]
            if laddr not in addr_map:
                addr_map[laddr] = idx
                distinct_addr_idx_sequence.append(idx)
                # -1表示负无穷
                reuse_distance = sys.maxint
            else:
                #当前addr出现过，那么计算上一次addr出现的位置到最后的距离即可
                old_idx = addr_map[laddr]
                last_distinct_location = distinct_addr_idx_sequence.index(old_idx)
                reuse_distance = len(distinct_addr_idx_sequence) - last_distinct_location - 1
                distinct_addr_idx_sequence.remove(old_idx)
                distinct_addr_idx_sequence.append(idx)
                addr_map[laddr] = idx

            if reuse_distance < sys.maxint:
                # 不记录第一次出现的addr
                output_fileobj.write("%d\n" % reuse_distance)
    output_fileobj.close()


if __name__ == "__main__":
    import sys
    import os
    if len(sys.argv) < 3:
        print("必须指定trace文件路径和输出结果路径!")
        sys.exit(0)
    if not os.path.isfile(sys.argv[1]) or not os.path.isdir(os.path.dirname(sys.argv[2])):
        print("%s: no such file or directory", sys.argv)
        sys.exit(0)
    print("Trace: %s\nResult:%s\n" % (sys.argv[1], sys.argv[2]))
    do_main(sys.argv[1], sys.argv[2])
    pass