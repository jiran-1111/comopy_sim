
import cocotb
from cocotb.clock import Clock  # 导入时钟驱动工具
from cocotb.triggers import RisingEdge,FallingEdge, Timer
import sys
import random
# ==============================================================================
# 1. 工具函数：按照 RISC‑V 手册 正确编码指令（和老师风格一致）
# ==============================================================================
def encode_rtype(rd, rs1, rs2, funct3, funct7):
    opcode = 0b0110011
    return (funct7 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode

def encode_itype(rd, rs1, imm12, funct3):
    opcode = 0b0010011
    imm12 &= 0xFFF
    return (imm12 << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode

# ==============================================================================
# 2. 专业测试1：测试 R-type 寄存器译码（老师测试核心）
# ==============================================================================
@cocotb.test()
async def test_decoder_rtype_regs(dut):
    # 指令：add x3, x7, x15
    inst = encode_rtype(rd=3, rs1=7, rs2=15, funct3=0b000, funct7=0b0000000)
    dut.inst.value = inst
    await Timer(1, "ns")

    assert dut.rd.value    == 3,   "rd error"
    assert dut.rs1.value   == 7,   "rs1 error"
    assert dut.rs2.value   == 15,  "rs2 error"
    assert dut.is_r_type.value == 1,"is_r_type error"
    assert dut.alu_sub.value == 0, "alu_sub error"
@cocotb.test()
async def test_decoder_alu_ops(dut):
    # ADD
    inst = encode_rtype(rd=1, rs1=2, rs2=3, funct3=0b000, funct7=0b0000000)
    dut.inst.value = inst
    await Timer(1, "ns")
    assert dut.alu_op.value == 0b000
    assert dut.alu_sub.value == 0
    assert dut.alu_sra.value == 0

    # SUB
    inst = encode_rtype(rd=1, rs1=2, rs2=3, funct3=0b000, funct7=0b0100000)
    dut.inst.value = inst
    await Timer(1, "ns")
    assert dut.alu_op.value == 0b000
    assert dut.alu_sub.value == 1
    assert dut.alu_sra.value == 0

    # SRL
    inst = encode_rtype(rd=1, rs1=2, rs2=3, funct3=0b101, funct7=0b0000000)
    dut.inst.value = inst
    await Timer(1, "ns")
    assert dut.alu_op.value == 0b101
    assert dut.alu_sub.value == 0
    assert dut.alu_sra.value == 0

    # SRA
    inst = encode_rtype(rd=1, rs1=2, rs2=3, funct3=0b101, funct7=0b0100000)
    dut.inst.value = inst
    await Timer(1, "ns")
    assert dut.alu_op.value == 0b101
    assert dut.alu_sub.value == 0   # 关键：这里应为 0，不是 1
    assert dut.alu_sra.value == 1   # SRA 应设置 alu_sra
# ==============================================================================
# 4. 专业测试3：测试 I-type 立即数指令
# ==============================================================================
@cocotb.test()
async def test_decoder_itype(dut):
    inst = encode_itype(rd=1, rs1=2, imm12=0x123, funct3=0b000)
    dut.inst.value = inst
    await Timer(1, "ns")

    assert dut.is_i_type.value == 1
    assert dut.alu_src2_imm.value == 1
    assert dut.rd.value == 1
    assert dut.rs1.value == 2


