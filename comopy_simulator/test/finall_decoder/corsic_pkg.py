from comopy.hdl import *

from spyre_base import EnumBase, PackedStruct 

class ALUOp(EnumBase):
    ADD  = 0b000
    SLL  = 0b001
    SLT  = 0b010
    SLTU = 0b011
    XOR  = 0b100
    SRL  = 0b101
    OR   = 0b110
    AND  = 0b111


class inst_op_t(PackedStruct):
    rs1          = Logic(5)
    rs2          = Logic(5)
    rd           = Logic(5)
    reg_write    = Logic()
    imm          = Logic(32)
    alu_op       = ALUOp()
    alu_sub      = Logic()
    alu_sra      = Logic()
    alu_src1_pc  = Logic()
    alu_src2_imm = Logic()
    is_branch    = Logic()
    is_jump      = Logic()