import cocotb
from cocotb.clock import Clock  # 导入时钟驱动工具
from cocotb.triggers import RisingEdge,FallingEdge, Timer
import sys
import random
"""
@cocotb.test()
async def adder_await__test(dut):
    await Timer(10, "ns")
    await Timer(15, "ns")
    await Timer(5, "ns")


"""
@cocotb.test()
async def adder_read_write_test(dut):
  
    for _ in range(10):
        # 随机抽取0~15的整数
        A = random.randint(0, 5)
        B = random.randint(0, 5)

        dut.a.value = A
        dut.b.value = B
  
        await Timer(2, unit="ns")
    
        # 输出和python的正确模型相匹配        
        assert dut.q.value == A + B, (
            f"Randomised test failed with: {dut.a.value} + {dut.b.value} = {dut.q.value}"
        )
"""
@cocotb.test()
async def adder_edge_test(dut):
    clock = Clock(dut.clk, 10, unit="ns") 
    cocotb.start_soon(clock.start())
    
    for _ in range(10):
        # 随机抽取0~15的整数
        A = random.randint(0, 15)
        B = random.randint(0, 15)

        dut.a.value = A
        dut.b.value = B
        await RisingEdge(dut.clk)
        #await Timer(1, "ns")
        await FallingEdge(dut.clk)
        await Timer(2, "ns")
    
        # 输出和python的正确模型相匹配        
        assert dut.q.value == A + B, (
            f"Randomised test failed with: {dut.a.value} + {dut.b.value} = {dut.q.value}"
        )
"""
