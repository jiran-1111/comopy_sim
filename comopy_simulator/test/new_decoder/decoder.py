"""
from comopy.hdl import *

class Decoder(Module):
    @build
    def ports(s):
        s.inst = Input(32)

        s.rd    = Output(5)
        s.rs1   = Output(5)
        s.rs2   = Output(5)
        s.is_r_type = Output(1)
        s.is_i_type = Output(1)
        s.is_lui    = Output(1)
        s.is_auipc  = Output(1)
        s.is_branch = Output(1)
        s.is_jump   = Output(1)

        s.alu_op     = Output(3)
        s.alu_sub    = Output(1)
        s.alu_sra    = Output(1)
        s.alu_src1_pc = Output(1)
        s.alu_src2_imm = Output(1)

        s.imm = Output(32)

    @comb
    def logic(s):
        # 指令类型
        s.is_r_type  /= (s.inst[2:7] == 0b01100)
        s.is_i_type  /= (s.inst[2:7] == 0b00100)
        s.is_lui     /= (s.inst[2:7] == 0b01101)
        s.is_auipc   /= (s.inst[2:7] == 0b00101)
        s.is_branch  /= (s.inst[2:7] == 0b11000)
        s.is_jump    /= (s.inst[2:7] == 0b11011)

        # 寄存器
        s.rd  /= s.inst[7:12]
        s.rs1 /= s.inst[15:20]
        s.rs2 /= s.inst[20:25]

        # 立即数符号扩展
        s.imm /= s.inst[20:32].S.ext(32)

        # ALU 操作
        if s.inst[12:15] == 0b000:
            s.alu_op /= 0b000
        elif s.inst[12:15] == 0b001:
            s.alu_op /= 0b001
        elif s.inst[12:15] == 0b010:
            s.alu_op /= 0b010
        elif s.inst[12:15] == 0b011:
            s.alu_op /= 0b011
        elif s.inst[12:15] == 0b100:
            s.alu_op /= 0b100
        elif s.inst[12:15] == 0b101:
            s.alu_op /= 0b101
        elif s.inst[12:15] == 0b110:
            s.alu_op /= 0b110
        elif s.inst[12:15] == 0b111:
            s.alu_op /= 0b111
        else:
            s.alu_op /= 0b000

        # ALU 控制信号
        s.alu_sub      /= s.inst[30]
        s.alu_sra      /= s.inst[30]
        s.alu_src1_pc  /= s.is_auipc | s.is_jump
        s.alu_src2_imm /= s.is_i_type
"""
from comopy import *
from comopy import RawModule, build, comb

class Decoder(RawModule):
    @build
    def ports(s):
        s.inst = Input(32)
        
        s.rd    = Output(5)
        s.rs1   = Output(5)
        s.rs2   = Output(5)
        
        s.is_r_type   = Output(1)
        s.is_i_type   = Output(1)
        s.is_s_type   = Output(1)
        s.is_b_type   = Output(1)
        s.is_u_type   = Output(1)
        s.is_j_type   = Output(1)
        s.is_lui      = Output(1)
        s.is_auipc    = Output(1)
        s.is_branch   = Output(1)
        s.is_jump     = Output(1)
        
        s.alu_op      = Output(3)
        s.alu_sub     = Output(1)
        s.alu_sra     = Output(1)
        s.alu_src1_pc = Output(1)
        s.alu_src2_imm= Output(1)
        
        s.imm         = Output(32)
        
        s.reg_write   = Output(1)
        s.mem_read    = Output(1)
        s.mem_write   = Output(1)
        s.mem_to_reg  = Output(1)

    @comb
    def logic(s):
        # ---------- 指令类型解码 ----------
        s.is_r_type   /= (s.inst[0:7] == 0b0110011)
        s.is_i_type   /= (s.inst[0:7] == 0b0010011)
        s.is_s_type   /= (s.inst[0:7] == 0b0100011)
        s.is_b_type   /= (s.inst[0:7] == 0b1100011)
        s.is_u_type   /= (s.inst[0:7] == 0b0110111) | (s.inst[0:7] == 0b0010111)
        s.is_j_type   /= (s.inst[0:7] == 0b1101111)
        
        s.is_lui      /= (s.inst[0:7] == 0b0110111)
        s.is_auipc    /= (s.inst[0:7] == 0b0010111)
        s.is_branch   /= s.is_b_type
        s.is_jump     /= s.is_j_type
        
        # ---------- 寄存器地址 ----------
        s.rd  /= s.inst[7:12]
        s.rs1 /= s.inst[15:20]
        s.rs2 /= s.inst[20:25]
        
        # ---------- 立即数生成 ----------
        s.imm /= 0
        if s.is_i_type == 1:
            s.imm /= s.inst[20:32].S.ext(32)
        if s.is_s_type == 1:
            s.imm /= cat(s.inst[25:32], s.inst[7:12]).S.ext(32)
        if s.is_b_type == 1:
            s.imm /= cat(s.inst[31], s.inst[7], s.inst[25:31], s.inst[8:12], b1(0)).S.ext(32)
        if s.is_u_type == 1:
            s.imm /= cat(s.inst[12:32], rep(12, b1(0)))
        if s.is_j_type == 1:
            s.imm /= cat(s.inst[31], s.inst[12:20], s.inst[20], s.inst[21:31], b1(0)).S.ext(32)
        
        # ---------- ALU 操作码 ----------
        s.alu_op /= 0b000
        if (s.is_r_type == 1) or (s.is_i_type == 1):
            if s.inst[12:15] == 0b000:
                s.alu_op /= 0b000
            elif s.inst[12:15] == 0b001:
                s.alu_op /= 0b001
            elif s.inst[12:15] == 0b010:
                s.alu_op /= 0b010
            elif s.inst[12:15] == 0b011:
                s.alu_op /= 0b011
            elif s.inst[12:15] == 0b100:
                s.alu_op /= 0b100
            elif s.inst[12:15] == 0b101:
                s.alu_op /= 0b101
            elif s.inst[12:15] == 0b110:
                s.alu_op /= 0b110
            elif s.inst[12:15] == 0b111:
                s.alu_op /= 0b111
        
        # ---------- ALU 控制信号 ----------
        s.alu_sub    /= ((s.is_r_type == 1) & (s.inst[12:15] == 0b000) & (s.inst[30] == 1)) | (s.is_b_type == 1)
        s.alu_sra    /= ((s.is_r_type == 1) | (s.is_i_type == 1)) & (s.inst[12:15] == 0b101) & (s.inst[30] == 1)
        s.alu_src1_pc /= (s.is_auipc == 1) | (s.is_jump == 1)
        s.alu_src2_imm /= (s.is_r_type == 0)
        
        # ---------- 访存与写回 ----------
        s.reg_write   /= ((s.is_r_type == 1) | (s.is_i_type == 1) | (s.is_lui == 1) | (s.is_auipc == 1) | (s.is_j_type == 1) | (s.inst[0:7] == 0b0000011))
        s.mem_read    /= (s.inst[0:7] == 0b0000011)
        s.mem_write   /= (s.is_s_type == 1)
        s.mem_to_reg  /= (s.inst[0:7] == 0b0000011)