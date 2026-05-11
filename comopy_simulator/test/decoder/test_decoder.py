import cocotb
from cocotb.triggers import Timer
import random

@cocotb.test()
async def test_decoder_simple(dut):
    """验证 R-type 指令译码"""
    
    # 构造一个 R-type 指令: add x3, x7, x15 (funct7=0, rs2=15, rs1=7, funct3=0, rd=3, op=0x33)
    # 指令二进制: 0000000_01111_00111_000_00011_0110011
    inst_val = 0x00f381b3 
    
    dut.inst.value = inst_val
    await Timer(2, "ns")

    # 验证输出
    assert int(dut.rd.value) == 3, f"RD 错误: {int(dut.rd.value)}"
    assert int(dut.rs1.value) == 7, f"RS1 错误: {int(dut.rs1.value)}"
    assert int(dut.is_r_type.value) == 1, "应该识别为 R-type"
    
    print("Decoder 基础功能测试通过！")

@cocotb.test()
async def test_random_instr(dut):
    """随机压力测试"""
    for _ in range(20):
        rd = random.randint(0, 31)
        rs1 = random.randint(0, 31)
        # 构造简单的 I-type 立即数指令 (仅演示字段截取)
        # 格式: imm[11:0], rs1, funct3, rd, opcode
        fake_inst = (0 << 20) | (rs1 << 15) | (0 << 12) | (rd << 7) | 0x13
        
        dut.inst.value = fake_inst
        await Timer(1, "ns")
        
        assert int(dut.rd.value) == rd
        assert int(dut.rs1.value) == rs1
        assert int(dut.is_imm.value) == 1