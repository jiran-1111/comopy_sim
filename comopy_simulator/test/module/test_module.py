import cocotb
from cocotb.clock import Clock  # 导入时钟驱动工具
from cocotb.triggers import RisingEdge, Timer,FallingEdge
import sys
import random

# 加法器的基本测试

@cocotb.test()
async def test_0(dut):
    
    # 所有带时钟的必须写这两行启动时钟
    clock = Clock(dut.clk, 10, unit="ns") 
    cocotb.start_soon(clock.start())
   
    await Timer(10, unit="ns") # 给时钟一点启动时间 
    #A = 2
    #B = 3
    #dut.a.value = A
    #dut.b.value = B
    await RisingEdge(dut.clk)
    await Timer(10, unit="ns")
    #await FallingEdge(dut.clk)
    print("Waiting for RisingEdge...")
    #print(f"Result q: {dut.q.value}") 
    #print(f"Result q_ff: {dut.q_ff.value}")
    #assert dut.q.value == A + B

"""

@cocotb.test()
async def test_edge(dut):
    # 既然是新测试，先确保 clk 是初始状态
    #dut.clk.value = 0 
    
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    
    # 不要用 Timer(1)，直接对齐到时钟周期
   
    await Timer(9, unit="ns") # 1001 + 9000 = 10001
    for i in range(10):
        print(f"Loop {i}: Waiting for Edge...")
        await RisingEdge(dut.clk)
        print(f"Loop {i}: Edge detected!")
"""