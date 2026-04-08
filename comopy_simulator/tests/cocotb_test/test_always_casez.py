import cocotb
from cocotb.triggers import Timer, RisingEdge

@cocotb.test()
async def test_priority_encoder(dut):
    """测试 Always_casez: 验证从低位开始的优先编码"""
    
    # 场景 1: 最低位为1，不管高位如何，pos 应该输出 0
    dut.in_.value = 0b10101011 
    await Timer(1, "ns")
    assert dut.pos.value == 0, "Should prioritize bit 0"
    
    # 场景 2: 第4位是第一个出现的1
    dut.in_.value = 0b11110000
    await Timer(1, "ns")
    assert dut.pos.value == 4, f"Should find bit 4, got {dut.pos.value}"
    
    # 场景 3: 全 0 应该走 default 情况 (s.pos /= 0)
    dut.in_.value = 0
    await Timer(1, "ns")
    assert dut.pos.value == 0