# my_hdl.py
from comopy import *

class SimpleDut(RawModule):
    def __init__(self):
        # 显式给它一个名字，方便 Simulator 识别
        super().__init__(name="SimpleDut")
        
    @build
    def ports(s):
        s.clk = Input(1)
        s.q   = Output(1)

    @comb
    def logic(s):
        s.q /= s.clk  # 至少有一条连线