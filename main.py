# coding=utf-8
__author__ = 'liuyix'


#todo implement
def do_main(filepath, outpath):
    trace = read_trace(filepath)
    sequence = count_distance(trace)
    write_result(sequence, outpath)


def write_result(sequence, outpath='foo-distance-sequence.out'):
    with open(outpath, 'w') as outfile:
        for s in sequence:
            outfile.write("%s\n" % s)

#todo implement
def read_trace(filename):
    #assert isinstance(filename) == str
    trace = []
    with open(filename) as fobj:
        #todo confirm the right input form of access address
        #trace = fobj.readlines()
        trace = [inst.split(':')[0] for inst in fobj]
    return trace
    pass


def count_distinct_element(trace, previous, current):
    #最原始的做法会有重复计算，因为每次都可能会计算相同的的位置
    if previous + 1 >= current:
        return 0
    elements = set()
    for t in trace[previous + 1:current]:
        elements.add(t)
    return len(elements)


#todo implement
def count_distance(trace):
    inst_dist = {}
    distance_sequence = []
    for linum, inst in enumerate(trace):
        if inst not in inst_dist:
            inst_dist[inst] = linum
        else:
            previous_linum = inst_dist[inst]
            distance = count_distinct_element(trace, previous_linum, linum)
            distance_sequence.append(distance)
    pass
    return distance_sequence


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