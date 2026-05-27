import cocotb
from cocotb.clock import Clock  # 导入时钟驱动工具
from cocotb.triggers import RisingEdge,FallingEdge, Timer
import sys


@cocotb.test()
async def adder_await__test(dut):
    await Timer(10, "ns")
    await Timer(15, "ns")
    await Timer(5, "ns")