import cocotb
from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock
"""
@cocotb.test()
async def test_andgate(dut):
    #测试 Andgate
    for a, b in [(0,0), (0,1), (1,0), (1,1)]:
        dut.a.value = a
        dut.b.value = b
        await Timer(1, "ns")
        assert dut.out.value == (a & b), f"Failed at {a},{b}"
"""

@cocotb.test()
async def test_andgate(dut):
    """测试 Andgate 并统计 100% 覆盖率"""
    # 1. 初始化 Bins (2x2=4 种组合)
    bins_cross = {(a, b): 0 for a in range(2) for b in range(2)}
    
    for a, b in [(0,0), (0,1), (1,0), (1,1)]:
        dut.a.value = a
        dut.b.value = b
        await Timer(1, "ns")
        
        # 2. 采样
        bins_cross[(a, b)] += 1
        assert dut.out.value == (a & b), f"Failed at {a},{b}"

    # 3. 报告
    covered = sum(1 for count in bins_cross.values() if count > 0)
    total = len(bins_cross)
    dut._log.info(f"Coverage: {covered}/{total} bins ({covered/total*100:.2f}%)")