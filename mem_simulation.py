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


class OnchipBase(object):
    def __init__(self, line_sz, total_sz, logger=None):
        assert isinstance(line_sz) is int \
                   and isinstance(total_sz) is int \
                   and line_sz > 0 \
            and total_sz > 0
        self.line_size = line_sz
        self.total_size = total_sz
        self.line_count = total_sz / line_sz
        if logger is None:
            from logger import setup_logging

            self.logger = setup_logging(filelog='mem_simulation.log')


class ScratchpadMemory(OnchipBase):
    def simulate(self, trace):
        """
        Input: trace[begin, end]
        Output: scratch pad memory miss ratio & cache miss ratio
        """
        memory_dict = {}
        for addr in trace:
            if addr in memory_dict:
                memory_dict[addr] += 1
            else:
                memory_dict[addr] = 1
        self.logger.info('memory instinct access count: %d', len(memory_dict))
        inst_list_result = sorted(memory_dict, key=memory_dict.get, reverse=True)
        # 当前采用的管理算法是计算得出该段中，访问频率最高的line_count个，之后只有整个trace段中访问时“预留”位置给这些地址
        # 因此缺失率直接可以通过计算得到，不用模拟。
        # 即缺失率=所有其他地址的访问总数 + line_count（首次访问缺失），因而可看出spm的效率和访问集中程度有关。
        trace_length = len(trace)
        hit_count = sum([memory_dict[addr] for addr in inst_list_result[:self.line_count]])
        return (trace_length - hit_count) / trace_length


class DataCache(OnchipBase):
    """
    associative: 表示相联配置,-1/0/2/4/8/16/,-1表示全相联
    暂时只实现组相联
    """

    def __init__(self, line_sz, total_sz, logger=None, associative=2):
        super(DataCache, self).__init__(line_sz, total_sz, logger)
        self.associative = associative

    def get_group_id(self, addr):
        return -1

    def simulate(self, trace):
        return 0.0


if __name__ == "__main__":
    import sys
    import os

    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        from logger import setup_logging

        logger = setup_logging(logfile='mem_simulation.log')
        pass
