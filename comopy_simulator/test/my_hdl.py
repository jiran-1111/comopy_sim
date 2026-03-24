from comopy.hdl import *

class SimpleDut(RawModule):
    @build
    def ports(s):
        s.a = Input(5)
        s.b = Input(5)
        s.q   = Output(5)

    @comb
    def logic(s):

        s.q /= s.a * s.b