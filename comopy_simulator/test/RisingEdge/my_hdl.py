from comopy.hdl import *

class SimpleDut(Module):
  
    @build
    def ports(s):
        
        s.a = Input(5)
        s.b = Input(5)
        s.q = Output(5)
        s.q_ff = Output(5)

    @comb
    def update(s):
        s.q /= s.a + s.b
    
    # 修复方案：使用字符串指定端口名
    # CoMoPy 会在后续的 build 阶段去 ports 里寻找匹配的名称
    @seq
    def update_ff(s):
        s.q_ff <<= s.a + s.b
    
