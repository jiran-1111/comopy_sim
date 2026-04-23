from comopy.hdl import *


class SimpleDut(Module):
  
    @build
    def ports(s):

        s.a = Input(5)
        s.b = Input(5)
        s.q = Output(5)
    
    @comb
    def update(s):
        s.q /= s.a + s.b
    """
    @seq
    def update_ff(s):
        s.q <<= s.a + s.b  # 使用 <<= 表示非阻塞赋值/时序更新
    """