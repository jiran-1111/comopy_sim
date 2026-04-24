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
from cocotb_coverage.coverage import CoverPoint, CoverCross, coverage_db

@CoverPoint("andgate.a", xf=lambda a, b, out: a, bins=[0, 1])
@CoverPoint("andgate.b", xf=lambda a, b, out: b, bins=[0, 1])
@CoverCross("andgate.input_cross", items=["andgate.a", "andgate.b"])
def sample_andgate(a, b, out):
    pass

@cocotb.test()
async def test_andgate(dut):
    for a, b in [(0,0), (0,1), (1,0), (1,1)]:
        dut.a.value = a
        dut.b.value = b
        await Timer(1, "ns")
        out = dut.out.value
        assert out == (a & b), f"Failed at {a},{b}"
        sample_andgate(a, b, out)

    coverage_db.report_coverage(dut._log.info)