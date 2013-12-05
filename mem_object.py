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
import logging


class OnchipBase(object):
    def __init__(self, line_sz, total_sz, logger=None, console=True, filelog=False, level=logging.ERROR):
        import sys
        assert isinstance(line_sz, int)  \
            and isinstance(total_sz, int)  \
            and line_sz > 0 \
            and total_sz > 0
        self.line_size = line_sz
        self.total_size = total_sz
        self.line_count = total_sz / line_sz
        if logger is None:
            from logger import setup_logging
            self.logger = setup_logging(console=console, logfile='mem_simulation.log', filelog=filelog, level=level)
        else:
            self.logger = logger
        self.line_szbit = int(math.log(self.line_size, 2))
        self.total_szbit = int(math.log(self.total_size, 2))

    def page_addr(self, vaddr):
        return vaddr & (sys.maxint << self.line_szbit)

    @staticmethod
    def extract_vaddr(line, simple_debug=False):
        assert isinstance(line, str)
        if not simple_debug:
            return long(line.split(':')[0].strip(), 16)
        return long(line, 16)


class ScratchpadMemory(OnchipBase):

    def hot_addr(self, trace):
        memory_dict = {}
        for line in trace:
            addr = self.extract_vaddr(line)
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
    遇到问题：做cache必须要用到phyaddr，不然不同进程的vaddr相同不是就错了！单个进程该假定是正确的。

    相联选址备忘：最后lg(linesize)位屏蔽，之后的lg(totalsz)-lg(linesz)-lg(associative)作为分组的id
        之后组内是set结构，大小为associative
    """

    def __init__(self, line_sz, total_sz, associative=4, logger=None, level=logging.ERROR):

        # line_size * associative * group_size = total_size
        super(DataCache, self).__init__(line_sz, total_sz, logger, level=level)
        self.associative = associative
        # 总共的组数
        self.group_total = self.line_count / self.associative
        group_id_bitlength = self.total_szbit - self.line_szbit - int(math.log(self.associative, 2))
        self.mask = (sys.maxint >> (int(math.log(sys.maxint, 2)) - group_id_bitlength))
        # pre allocation
        self.__list = [None] * self.group_total
        self.logger.debug('cache list: %s',self.__list)
        self.hit_cnt = 0.0
        self.access_cnt = 0.0
        self.swap_cnt = 0.0

    def reset(self):
        self.hit_cnt = 0.0
        self.access_cnt = 0.0
        self.swap_cnt = 0.0
        self.__list = [None] * self.group_total

    def hit_ratio(self):
        if self.access_cnt == 0:
            return -1
        return self.hit_cnt / self.access_cnt

    def miss_ratio(self):
        if self.access_cnt == 0:
            self.logger.warn("total access is 0!")
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
        gid = (vaddr >> self.line_szbit) & self.mask
        return gid

    def access(self, vaddr):
        """
        group_set None
        """
        gid = self.group_id(vaddr)
        self.logger.debug('=' * 80)
        self.logger.debug('vaddr: %s', bin(vaddr))
        self.logger.debug('gid: %s', bin(gid))
        group_set = self.__list[gid]
        if group_set is None:
            self.__list[gid] = set()
            group_set = self.__list[gid]
        assert len(group_set) <= self.associative
        self.access_cnt += 1
        page_addr = self.page_addr(vaddr)

        self.logger.debug('group set content: \n%s', group_set)

        if page_addr in group_set:
            self.logger.debug("hit: page_addr: %s", bin(page_addr))
            self.hit_cnt += 1
            return True
        elif len(group_set) < self.associative:
            self.logger.debug('miss: page_addr: %s, add directly', bin(page_addr))
            group_set.add(page_addr)
        else:
            self.logger.debug('miss: page_addr: %s, swap', bin(page_addr))
            laddr = group_set.pop()
            self.logger.debug("swap: %s", bin(laddr))
            group_set.add(page_addr)
            self.swap_cnt += 1
        return False

    def simulate(self, trace):
        assert isinstance(trace, list)

        for line in trace:
            vaddr = self.extract_vaddr(line)
            self.access(vaddr)
        return self.miss_ratio()


class HybridCache:
    def __init__(self, spm_size, spm_linesize, cache_size, cacheline_size, associative, logger=None, level=logging.ERROR):
        assert not (spm_size == 0 and cache_size == 0)
        if spm_size != 0:
            self.__spm = ScratchpadMemory(spm_linesize, spm_size, logger=logger)
        else:
            self.__spm = None
        if cache_size != 0:
            self.__dcache = DataCache(cacheline_size, cache_size, associative=associative, logger=logger, level=level)
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
                trace_cache = \
                    filter(lambda x: OnchipBase.extract_vaddr(x) not in inst_list[:self.__spm.line_count], trace)
                #logger.debug('trace size: %d\treduced size: %d' % (len(trace), len(trace_cache)))
                cache_miss = self.__dcache.simulate(trace_cache)
        else:
            cache_miss = self.__dcache.simulate(trace)
        return spm_miss, cache_miss




def test_cache():
    f = open('./phase-1', 'r')
    lines = f.readlines()
    dc = DataCache(64, 32 * 1024, 4, level=logging.ERROR)
    dc.simulate(lines)
    print 'miss: ', dc.miss_ratio()
    print 'total hit: ', dc.hit_cnt
    print 'total access: ', dc.access_cnt

if __name__ == "__main__":
    import sys
    test_cache()
