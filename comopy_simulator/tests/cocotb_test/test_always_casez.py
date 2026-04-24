import cocotb
from cocotb.triggers import Timer, RisingEdge
"""
@cocotb.test()
async def test_priority_encoder(dut):
    #测试 Always_casez: 验证从低位开始的优先编码
    
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

"""
from cocotb_coverage.coverage import CoverPoint, CoverCross, coverage_db
# ============================
# 1. 优先编码器 Priority Encoder
# ============================
@CoverPoint("encoder.output_pos", xf=lambda in_val, pos: pos, bins=list(range(8)))
@CoverPoint("encoder.all_zero", xf=lambda in_val, pos: in_val == 0, bins=[True, False])
def sample_encoder(in_val, pos):
    pass

@cocotb.test()
async def test_priority_encoder(dut):
    test_cases = [
        (0b10101011, 0),
        (0b11110000, 4),
        (0b00000000, 0),
        (0b00000010, 1),
        (0b00000100, 2),
        (0b00001000, 3),
        (0b00100000, 5),
        (0b01000000, 6),
        (0b10000000, 7),
    ]

    for val, expected_pos in test_cases:
        dut.in_.value = val
        await Timer(1, "ns")
        assert dut.pos.value == expected_pos, f"Failed at {bin(val)}"
        sample_encoder(val, expected_pos)

    coverage_db.report_coverage(dut._log.info)