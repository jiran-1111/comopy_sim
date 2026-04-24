import cocotb
from cocotb.triggers import Timer
"""
@cocotb.test()
async def test_parity_reduction(dut):
    #测试 Reduction: 验证 8位奇偶校验
    # .P 运算通常是异或缩减 (XOR reduction)
    test_cases = [
        (0b00000000, 0), # 偶数个1
        (0b00000001, 1), # 奇数个1
        (0b10101010, 0), # 4个1 (偶数)
        (0b11111111, 0), # 8个1 (偶数)
        (0b11100000, 1), # 3个1 (奇数)
    ]
    
    for val, expected_parity in test_cases:
        dut.in_.value = val
        await Timer(1, "ns")
        assert dut.parity.value == expected_parity, f"Failed at {bin(val)}"

"""
from cocotb_coverage.coverage import CoverPoint, CoverCross, coverage_db
@CoverPoint("parity.type", xf=lambda in_val, p: p, bins=[0, 1])
def sample_parity(in_val, p):
    pass

@cocotb.test()
async def test_parity_reduction(dut):
    test_cases = [
        (0b00000000, 0),
        (0b00000001, 1),
        (0b10101010, 0),
        (0b11111111, 0),
        (0b11100000, 1),
    ]

    for val, expected_p in test_cases:
        dut.in_.value = val
        await Timer(1, "ns")
        assert dut.parity.value == expected_p, f"Failed at {bin(val)}"
        sample_parity(val, expected_p)

    coverage_db.report_coverage(dut._log.info)

