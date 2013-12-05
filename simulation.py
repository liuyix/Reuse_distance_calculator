#coding:utf-8
__author__ = 'liuyix'

from mem_object import DataCache, HybridCache, ScratchpadMemory, extract_vaddr
from logger import setup_logging
import logging
from csv_helper import CsvHelper

#phase_id = 0


def test_cache(phase, writer):
    #global phase_id
    #with open('phase-%d' % phase_id, 'w') as pf:
    #    for l in phase:
    #        vaddr = extract_vaddr(l)
    #        pf.write(hex(vaddr))
    #        pf.write('\n')
    #    phase_id += 1
    for totalsz in [4, 8, 16, 32, 64, 128]:
        #for linesz in [32, 64, 128, 256, 512]:
        for linesz in [32, 64, 128, 256, 512]:
            print 'total: %d\nline:%d' % (totalsz, linesz)
            dc = DataCache(linesz, totalsz << 10, associative=4)
            miss = dc.simulate(phase)
            print 'miss: %f' % miss
            print 'hit_cnt: %d' % dc.hit_cnt
            writer.write([str(totalsz), str(linesz), str(miss)])


def test_hybrid(phase, writer):
    print '=' * 80
    print 'SPM + Cache'
    onchip_total = 256
    for spm_total in [16, 32, 64, 128, 256]:
        for blksz in [16, 32, 64, 128]:
            dcache_size = onchip_total - spm_total
            dcache_line = blksz
            print 'total: %dKB, line:%dB' % (spm_total, blksz)
            print 'dcache size: %dKB, line: %dB' % (dcache_size, dcache_line)
            hc = HybridCache(spm_total << 10, blksz, dcache_size << 10,dcache_line, 4, level=logging.ERROR)
            spm_miss, cache_miss = hc.simulate(phase)
            print 'spm miss: %.3f, cache miss: %.3f' % (spm_miss, cache_miss)
            writer.write([str(num) for num in [spm_total, blksz, spm_miss, dcache_size, dcache_line, cache_miss]])


def is_close(total, pre, cur):
    return float(cur - pre) < total * 0.05


def filter_result_parser(result_file='./simple_matrix/filtered.out'):
    """
    输出：ratio segments, e.g. [[0.3, 0.5], [0.5, 0.7]]
    筛选逻辑：
        如下
        121,123,431,437,439,1000,1002,1010,2000,2002
        结果：
        123, 431, 439, 1000, 1010, 2000, 2002
    """
    f = open(result_file, 'r')
    lines = f.readlines()
    line_count = 0
    numbers = []
    pre_no = -1
    for n, l in enumerate(lines):
        if n == 0:
            assert l.split('\t')[0].strip() == 'length'
            line_count = int(l.split('\t')[1].strip())
        if n > 3:
            cur_no = int(l.split('\t')[1].strip())
            if pre_no == -1:
                pre_no = cur_no
            else:
                if is_close(line_count, pre_no, cur_no):
                    if len(numbers) % 2 == 0:
                        # 是偶数，则说明现在numbers里面最后一个元素是上一段的后边界值
                        numbers.append(cur_no)
                    else:
                        # 是奇数，则说明是新段的首边界值
                        numbers[len(numbers)-1] = cur_no
                else:
                    numbers.append(cur_no)
                pre_no = cur_no
    #for n in numbers:
    #    print n
    # 实现两两配对组成tuple
    numbers = [float(n) / line_count for n in numbers]
    tuples = zip(numbers[::2], numbers[1::2])
    #print tuples
    return tuples


def extract_phases(lines, line_count):
    phase_boudaries = filter_result_parser()
    phases = []
    for b in phase_boudaries:
        begin = int(b[0] * line_count)
        end = int(b[1] * line_count)
        print begin
        print end
        phases.append(lines[begin:end])
    return phases


def wccount(filename):
    import subprocess
    out = subprocess.Popen(['wc', '-l', filename],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT
    ).communicate()[0]
    return int(out.partition(b' ')[0])


def simulate_main(trace_name='./simple_matrix/thread0-trace.out', hybrid=True, cache=True, spm=False):
    line_count = wccount(trace_name)
    trace_fobj = open(trace_name, 'r')
    phases = extract_phases(trace_fobj.readlines(), line_count)
    i = 0
    for p in phases:
        i += 1
        csvhelper = CsvHelper('phase-%d.csv' % i)
        print '--------------------------------'
        print 'length: %d' % len(p)
        if hybrid:
            csvhelper.write(['spm total', 'spm block', 'spm miss', 'cache total', 'cache line', 'cache miss'])
            test_hybrid(p, csvhelper)
        if cache:
            csvhelper.write(['cache size', 'cache line', 'miss'])
            test_cache(p, csvhelper)
    trace_fobj.close()


def simple_trace():
    trace='./simple_matrix/thread0-trace.out'
    trace_file = open(trace, 'r')
    file_line_count = wccount(trace)
    trace_begin = int(68365.0 / 268569.0 * file_line_count)
    trace_end = int(151920.0 / 268569.0 * file_line_count)
    phase = trace_file.readlines()[trace_begin:trace_end]

    logger.info("line count: %d", file_line_count)
    logger.info("begin: %d, end: %d", trace_begin, trace_end)
    return phase

if __name__ == "__main__":
    import sys

    from logger import setup_logging
    logger = setup_logging(console=False, logfile='mem_simulation.log')
    #do_simple_test()
    #test_cache()
    #filter_result_parser()
    #extract_phases()
    simulate_main()