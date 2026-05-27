
from comopy.hdl import *

from corsic_pkg import ALUOp, inst_op_t
from riscv_pkg import inst_t, inst_rtype_t


class Decoder(RawModule):
 
    @build
    def ports(s):
        s.inst = Input()
        s.inst_op = Output()

    @build
    def fields(s):
        # R-type instruction
        s.rtype = inst_rtype_t()
        s.rtype @= s.inst

        # opcode[0:2]==0b11 for 32-bit instructions, others for RVC
        s.opcode5 = Logic(5)
        s.opcode5 @= s.rtype.opcode[2:]

        # ALU operation type
        s.alu_op = ALUOp()

    @build
    def decode_type(s):
        # Format types
        s.is_r_type = Logic()
        s.is_i_type = Logic()
        s.is_s_type = Logic()
        s.is_b_type = Logic()
        s.is_u_type = Logic()
        s.is_j_type = Logic()

        # Special instructions
        s.is_lui = Logic()
        s.is_auipc = Logic()

        # Decode instruction format based on opcode[6:2].
        s.is_r_type @= s.opcode5 == 0b01100
        s.is_i_type @= s.opcode5 == 0b00100
        s.is_s_type @= s.opcode5 == 0b01000
        s.is_b_type @= s.opcode5 == 0b11000
        s.is_lui @= s.opcode5 == 0b01101
        s.is_auipc @= s.opcode5 == 0b00101
        s.is_u_type @= s.is_lui | s.is_auipc
        s.is_j_type @= s.opcode5 == 0b11011

    @build
    def decode_regs(s):
        s.inst_op.rd @= s.rtype.rd
        s.inst_op.rs1 @= s.rtype.rs1
        s.inst_op.rs2 @= s.rtype.rs2
        s.inst_op.reg_write @= 1

    @build
    def decode_imm(s):
        # I-format: inst[31:20] sign-extended to 32 bits
        s.imm_i = hdl.Logic(32)
        s.imm_i @= s.inst[20:32].S.ext(32)

        s.inst_op.imm @= s.imm_i if s.is_i_type else 0

    @build
    def decode_alu(s):
        s.inst_op.alu_op @= s.alu_op
        s.inst_op.alu_sub @= s.rtype.funct7[5]
        s.inst_op.alu_sra @= s.rtype.funct7[5]
        s.inst_op.alu_src1_pc @= s.is_auipc | s.is_j_type
        s.inst_op.alu_src2_imm @= s.is_i_type
        s.inst_op.is_branch @= s.is_b_type
        s.inst_op.is_jump @= s.is_j_type

    @comb
    def decode_alu_op(s):
        match s.rtype.funct3:
            case 0b000:
                s.alu_op /= ALUOp.ADD
            case 0b001:
                s.alu_op /= ALUOp.SLL
            case 0b010:
                s.alu_op /= ALUOp.SLT
            case 0b011:
                s.alu_op /= ALUOp.SLTU
            case 0b100:
                s.alu_op /= ALUOp.XOR
            case 0b101:
                s.alu_op /= ALUOp.SRL
            case 0b110:
                s.alu_op /= ALUOp.OR
            case 0b111:
                s.alu_op /= ALUOp.AND
