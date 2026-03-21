from comopy.hdl import *

class SimpleDut(RawModule):
    @build
    def ports(s):
        s.a = Input(3)
        s.q   = Output(3)

    @comb
    def logic(s):

        s.q /= s.a