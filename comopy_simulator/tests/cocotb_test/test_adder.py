
import cocotb
from cocotb.clock import Clock  # 导入时钟驱动工具
from cocotb.triggers import RisingEdge, Timer,FallingEdge
import sys
import random

# 加法器的基本测试

@cocotb.test()
async def dut_0(dut):
    clock = Clock(dut.clk, 10, unit="ns") 
    cocotb.start_soon(clock.start())
    
    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    #print("Detected first edge!")
    await RisingEdge(dut.clk)
    #print("Detected second edge!")
    await Timer(1, "ns")


@cocotb.test()
async def dut_1(dut):
    clock = Clock(dut.clk, 10, unit="ns") 
    cocotb.start_soon(clock.start())
    
    await RisingEdge(dut.clk)
    #await Timer(1, "ns")
    #print("Detected first edge!")
    await FallingEdge(dut.clk)
    #print("Detected second edge!")
    await Timer(1, "ns")