import cocotb
from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock

@cocotb.test()
async def test_andgate(dut):
    """测试 Andgate"""
    for a, b in [(0,0), (0,1), (1,0), (1,1)]:
        dut.a.value = a
        dut.b.value = b
        await Timer(1, "ns")
        assert dut.out.value == (a & b), f"Failed at {a},{b}"