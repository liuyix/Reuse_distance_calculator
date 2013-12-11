# coding: utf-8
__author__ = 'liuyix'


class Trace:
    def __init__(self, trace_file):
        import os
        assert os.path.exists(trace_file) and os.path.isfile(trace_file)
        self.file = trace_file
        self.tf = open(trace_file, 'r')

    def __del__(self):
        if self.tf is not None:
            self.tf.close()
            self.tf = None


def extract_vaddr(line, simple_debug=False):
    assert isinstance(line, str)
    if not simple_debug:
        return long(line.split(':')[0].strip(), 16)
    return long(line, 16)


def extract_rwflag(line, simple_debug=False):
    if not simple_debug:
        return line.split(':')[2].strip()
    return line.split(':')[1].strip()
    pass


def test(trace_file):
    import os
    assert os.path.exists(trace_file) and os.path.isfile(trace_file)
    with open(trace_file, 'r') as tf:
        for l in tf.readlines()[:10]:
            print hex(extract_vaddr(l))
            print extract_rwflag(l)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        print "filename: %s" % sys.argv[1]
        test(sys.argv[1])
    else:
        print 'You need specify a trace file'