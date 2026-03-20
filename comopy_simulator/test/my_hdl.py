from comopy.hdl import *

class SimpleDut(RawModule):
    @build
    def ports(s):
        s.a = Input(1)
        s.q   = Output(1)

    @comb
    def logic(s):

        s.q /= s.a