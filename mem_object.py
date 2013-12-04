#coding:utf-8
__author__ = 'liuyix'

# 关于计算命中率，可以一次遍历trace，把所有的模拟都算出来，不同配置只是参数不同而已。
# 对spm而言，需要遍历一次，计算出不同block大小时，一段trace中的访问热点排序结果（如1kB,2kB...）
# 对cache而言，需要根据配置计算不同的组地址
# 首先需要修改pin工具，确保trace不是block单位获取的。
# 之后重新跑reuse_distance，matlab以及trace分段
# 第三，trace分段工具实现根据filtered.out选出最终的*分段点*
# 另外的优化的地方是多线程的读trace，可以并行的进行模拟，即纯cache、纯spm、cache+spm(前继任务是纯spm，需要一次遍历得到不同粒度的访存热点地址)
# 得到的实验输出做成csv格式或者是用matplotlib直接成图。

import math


class OnchipBase(object):
    def __init__(self, line_sz, total_sz, logger=None, console=True, filelog=False):
        assert isinstance(line_sz, int)  \
            and isinstance(total_sz, int)  \
            and line_sz > 0 \
            and total_sz > 0
        self.line_size = line_sz
        self.total_size = total_sz
        self.line_count = total_sz / line_sz
        if logger is None:
            from logger import setup_logging
            self.logger = setup_logging(console=console, logfile='mem_simulation.log', filelog=filelog)
        else:
            self.logger = logger
        self.line_szbit = int(math.log(self.line_size, 2))
        self.total_szbit = int(math.log(self.total_size, 2))

    def page_addr(self, vaddr):
        return vaddr & (sys.maxint << self.line_szbit)


class ScratchpadMemory(OnchipBase):

    def hot_addr(self, trace):
        memory_dict = {}
        for line in trace:
            addr = extract_vaddr(line)
            page_addr = self.page_addr(addr)
            if page_addr in memory_dict:
                memory_dict[page_addr] += 1
            else:
                memory_dict[page_addr] = 1
        #self.logger.info('memory instinct access count: %d', len(memory_dict))
        inst_list_result = sorted(memory_dict, key=memory_dict.get, reverse=True)
        #self.logger.debug('inst result: %s', inst_list_result[:self.line_count])
        return inst_list_result, memory_dict

    def simulate(self, trace):
        """
        Input: trace[begin, end]
        Output: scratchpad memory miss ratio & cache miss ratio
        """
        # 当前采用的管理算法是计算得出该段中，访问频率最高的line_count个，之后只有整个trace段中访问时“预留”位置给这些地址
        # 因此缺失率直接可以通过计算得到，不用模拟。
        # 即缺失率=所有其他地址的访问总数 + line_count（首次访问缺失），因而可看出spm的效率和访问集中程度有关。
        inst_list_result, memory_dict = self.hot_addr(trace)
        trace_length = len(trace)
        hit_count = sum([memory_dict[addr] for addr in inst_list_result[:self.line_count]])
        #self.logger.debug('hit count: %d', hit_count)
        miss = float(trace_length - hit_count) / trace_length
        #self.logger.info("miss ratio: %f", miss)
        return miss


class DataCache(OnchipBase):

    """
    associative: 表示相联配置,-1/0/2/4/8/16/,-1表示全相联
    暂时只实现组相联
    遇到问题：做cache必须要用到phyaddr，不然不同进程的vaddr相同不是就错了！
    """

    def __init__(self, line_sz, total_sz, associative=4, logger=None):

        # line_size * associative * group_size = total_size
        super(DataCache, self).__init__(line_sz, total_sz, logger)
        self.associative = associative
        # 总共的组数
        self.group_count = self.line_count / self.associative
        self.group_szbit = int(math.log(self.group_count, 2))
        # pre allocation
        self.__list = [set()] * self.group_count
        self.hit_cnt = 0.0
        self.access_cnt = 0.0
        self.swap_cnt = 0.0

    def reset(self):
        self.hit_cnt = 0.0
        self.access_cnt = 0.0
        self.swap_cnt = 0.0
        self.__list = [set()] * self.group_count

    def hit_ratio(self):
        if self.access_cnt == 0:
            return -1
        return self.hit_cnt / self.access_cnt

    def miss_ratio(self):
        if self.access_cnt == 0:
            return -1
        return 1 - self.hit_ratio()

    def swap_ratio(self):
        if self.access_cnt == 0:
            return -1
        else:
            return self.swap_cnt / self.access_cnt

    def group_id(self, vaddr):
        assert isinstance(vaddr, long)
        # 取vaddr的低log(cache_size)位,高位清零
        cache_addr = vaddr & (sys.maxint >> (int(math.log(sys.maxint, 2)) - self.total_szbit))
        return cache_addr >> (self.line_szbit + self.group_szbit)

    def access(self, vaddr):
        gid = self.group_id(vaddr)
        group_set = self.__list[gid]
        assert len(group_set) <= self.group_count

        self.access_cnt += 1
        page_addr = self.page_addr(vaddr)
        if page_addr in group_set:
            self.hit_cnt += 1
            return True
        elif len(group_set) < self.group_count:
            group_set.add(page_addr)
        else:
            group_set.pop()
            group_set.add(page_addr)
            self.swap_cnt += 1
        return False

    def simulate(self, trace):
        assert isinstance(trace, list)

        for line in trace:
            vaddr = extract_vaddr(line)
            self.access(vaddr)
        #print 'Cache Miss ratio: %.3f' % self.miss_ratio()
        return self.miss_ratio()


class HybridCache:
    def __init__(self, spm_size, spm_linesize, cache_size, cacheline_size, associative, logger=None):
        assert not (spm_size == 0 and cache_size == 0)
        if spm_size != 0:
            self.__spm = ScratchpadMemory(spm_linesize, spm_size, logger=logger)
        else:
            self.__spm = None
        if cache_size != 0:
            self.__dcache = DataCache(cacheline_size, cache_size, associative=associative, logger=logger)
        else:
            self.__dcache = None

    def simulate(self, trace):
        spm_miss = 1.0
        cache_miss = 1.0
        if self.__spm is not None:
            inst_list, inst_dict = self.__spm.hot_addr(trace)
            #print 'spm miss ratio: %.3f' % self.__spm.simulate(trace)
            spm_miss = self.__spm.simulate(trace)
            # http://stackoverflow.com/a/1157160
            # remove all occurences in list
            if self.__dcache is not None:
                trace_cache = filter(lambda x: extract_vaddr(x) not in inst_list[:self.__spm.line_count], trace)
                #logger.debug('trace size: %d\treduced size: %d' % (len(trace), len(trace_cache)))
                cache_miss = self.__dcache.simulate(trace_cache)
        else:
            cache_miss = self.__dcache.simulate(trace)
        return spm_miss, cache_miss


def extract_vaddr(line):
    assert isinstance(line, str)
    return long(line.split(':')[0].strip(), 16)


def do_simple_test(trace='./simple_matrix/thread0-trace.out'):
    trace_file = open(trace, 'r')

    file_line_count = wccount(trace)
    trace_begin = int(68365.0 / 268569.0 * file_line_count)
    trace_end = int(151920.0 / 268569.0 * file_line_count)
    phase = trace_file.readlines()[trace_begin:trace_end]

    logger.info("line count: %d", file_line_count)
    logger.info("begin: %d, end: %d", trace_begin, trace_end)

    # output settings
    from csv_helper import CsvHelper
    csvhelper = CsvHelper('matrix-result.csv')

    csvhelper.write_row(('spm_size(KB)', 'spm_block_size', 'cache_size(KB)',
                         'cache_line_size', 'associative', 'spm_miss', 'cache_miss'))
    for spmsize in [0, 4, 8, 16, 32]:
        #for blksz in [32, 64, 128]:
        blksz = 256
        #cache_totalsz = (256 - spmsize) * 1024
        cache_totalsz = (32 - spmsize) * 1024
        spmsize *= 1024
        cache_linesz = 64
        hybrid = HybridCache(spmsize, blksz, cache_totalsz, cache_linesz, 4)
        #hybrid = HybridCache(spmsize * 256, blksz, cache_totalsz * 256, cache_linesz, 4)
        spm_miss, cache_miss = hybrid.simulate(phase)
        print '------------------------------------------------------'
        print 'Configuration:'
        print 'Scratchpad size: %dKB\tblock:%d\nCache size:%dKB\tblock: %d' \
              % (spmsize / 1024, blksz, cache_totalsz / 1024, cache_linesz)

        print 'spm_miss: %.3f\tcache_miss: %.3f' % (spm_miss, cache_miss)
        csvhelper.write_row([str(n) for n in [spmsize/1024, blksz,
                           cache_totalsz/1024, cache_linesz, 4, spm_miss, cache_miss]])


def wccount(filename):
    import subprocess
    out = subprocess.Popen(['wc', '-l', filename],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT
    ).communicate()[0]
    return int(out.partition(b' ')[0])


if __name__ == "__main__":
    import sys

    from logger import setup_logging
    logger = setup_logging(console=False, logfile='mem_simulation.log')
    do_simple_test()
    #if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
    #    from logger import setup_logging
    #    logger = setup_logging(logfile='mem_simulation.log')
    #    do_simple_test()
    #    pass
