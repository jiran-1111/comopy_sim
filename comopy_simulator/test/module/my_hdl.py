from comopy.hdl import *

# 改为继承 Module
class SimpleDut(RawModule):
    
    @build
    def ports(s):
        s.clk = Input(1)
        s.a = Input(5)
        s.b = Input(5)
        s.q = Output(5)
        s.q_ff = Output(5)

    @comb
    def update(s):
        s.q /= s.a + s.b
    
    @seq
    def update_ff(s,posedge="clk"):
        # 在 Module 中，@seq 默认监听内置的 s.clk
        s.q_ff <<= s.a + s.b