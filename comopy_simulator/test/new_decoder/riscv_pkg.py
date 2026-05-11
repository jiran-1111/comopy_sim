# riscv_pkg.py
from comopy.hdl import *

class ALUOp:
    ADD  = 0b000
    SLL  = 0b001
    SLT  = 0b010
    SLTU = 0b011
    XOR  = 0b100
    SRL  = 0b101
    OR   = 0b110
    AND  = 0b111