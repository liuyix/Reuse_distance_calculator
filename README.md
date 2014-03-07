计算Reuse distance脚本
=========================

1. 使用pin工具得到_foo.trace_
1. 适当修改`main.py`中的`get_vaddr`使之能够正确解析每一行的访存虚存地址
2. python main.py foo.trace foo.trace.dist
