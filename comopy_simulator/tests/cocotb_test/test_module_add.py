import cocotb
from cocotb.triggers import Timer

@cocotb.test()
async def test_add32_simple(dut):
    """测试 32 位加法器基本功能"""
    # 场景 1: 普通加法
    dut.a.value = 0x12345678
    dut.b.value = 0x11111111
    await Timer(1, "ns")
    assert dut.sum.value == 0x23456789

    # 场景 2: 验证低 16 位向高 16 位的进位
    # 0x0000FFFF + 1 = 0x00010000
    dut.a.value = 0x0000FFFF
    dut.b.value = 0x00000001
    await Timer(1, "ns")
    assert dut.sum.value == 0x00010000, f"进位错误: {hex(int(dut.sum.value))}"

    # 场景 3: 边界测试 (全 F)
    dut.a.value = 0xFFFFFFFF
    dut.b.value = 0x00000001
    await Timer(1, "ns")
    # 32位加法溢出后应该为 0
    assert dut.sum.value == 0x00000000