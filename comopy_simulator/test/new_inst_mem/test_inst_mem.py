import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer, ClockCycles

async def reset_dut(dut):
    cocotb.start_soon(Clock(dut.clk, 10, "ns").start())
    await ClockCycles(dut.clk, 2)
    dut.req.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)

@cocotb.test()
async def t_reset_async(dut):
    dut.req.value = 1
    dut.addr.value = 0x100
    dut.rst_n.value = 0
    await Timer(1, "ns")
    assert dut.ready.value == 1
    assert dut.valid.value == 0

@cocotb.test()
async def t_request_single(dut):
    await reset_dut(dut)
    await RisingEdge(dut.clk)
    dut.mem[0].value = 0xDB000000
    dut.req.value = 1
    dut.addr.value = 0
    await RisingEdge(dut.clk)
    dut.req.value = 0
    await RisingEdge(dut.clk)
    assert dut.valid.value == 1
    assert dut.data.value == 0xDB000000