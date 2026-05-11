
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

# ==============================================================================
# 3. 专业测试2：测试 ALU 操作译码 ADD / SUB / SRL / SRA 等
# ==============================================================================
@cocotb.test()
async def test_decoder_alu_ops(dut):
    test_cases = [
        (0b000, 0b0000000, 0b000, 0), # ADD
        (0b000, 0b0100000, 0b000, 1), # SUB
        (0b101, 0b0000000, 0b101, 0), # SRL
        (0b101, 0b0100000, 0b101, 1), # SRA
    ]

    for funct3, funct7, exp_aluop, exp_sub in test_cases:
        inst = encode_rtype(rd=1, rs1=2, rs2=3, funct3=funct3, funct7=funct7)
        dut.inst.value = inst
        await Timer(1, "ns")
        assert dut.alu_op.value == exp_aluop
        assert dut.alu_sub.value == exp_sub

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

# ==============================================================================
# 5. 时序测试（保留你原来的风格）
# ==============================================================================
@cocotb.test()
async def test_decoder_with_clock(dut):
    Clock(dut.clk, 10, "ns").start()

    for _ in  range(5):
        inst = encode_rtype(rd=5, rs1=6, rs2=7, funct3=0, funct7=0)
        dut.inst.value = inst
        await RisingEdge(dut.clk)
        await Timer(1, "ns")
        assert dut.rd.value == 5
        assert dut.rs1.value == 6

# ==============================================================================
# 6. 运行入口
# ==============================================================================
import os
import sys
from cocotb_tools.runner import get_runner

def main():
    runner = get_runner("comopy")
    runner.build(
        sources=["decoder.py"],
        hdl_toplevel="Decoder"
    )
    runner.test(
        hdl_toplevel="Decoder",
        test_module="test_decoder"
    )

if __name__ == "__main__":
    main()