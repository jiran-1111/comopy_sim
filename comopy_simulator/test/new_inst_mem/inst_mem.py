from comopy.hdl import *

class InstMemSync(Module):
    def build_params(s):
        s.ADDR_WIDTH = 32
        s.MEM_DEPTH  = 1024

    def build(s):
        # 计算地址位宽
        s.MEM_ADDR_WIDTH = 0
        while (1 << s.MEM_ADDR_WIDTH) < s.MEM_DEPTH:
            s.MEM_ADDR_WIDTH += 1

        # ---------------------------
        # ComoPy 0.6.0 必须这样加端口
        # ---------------------------
        s.add_port("clk",   Dir.IN, 1)
        s.add_port("rst_n", Dir.IN, 1)
        s.add_port("req",   Dir.IN, 1)
        s.add_port("addr",  Dir.IN, s.ADDR_WIDTH)
        
        s.add_port("ready", Dir.OUT, 1)
        s.add_port("valid", Dir.OUT, 1)
        s.add_port("data",  Dir.OUT, 32)

        # 存储器
        s.mem = [Wire(32) for _ in range(s.MEM_DEPTH)]

        # 寄存器
        s.valid_q = Wire(1)
        s.data_q  = Wire(32)

        # 组合逻辑赋值
        s.ready.assign(1)
        s.valid.assign(s.valid_q)
        s.data.assign(s.data_q)

    def seq(s):
        if s.rst_n == 0:
            s.valid_q <= 0
        else:
            s.valid_q <= s.req
            s.data_q  <= s.mem[s.addr[2 : 2 + s.MEM_ADDR_WIDTH]]