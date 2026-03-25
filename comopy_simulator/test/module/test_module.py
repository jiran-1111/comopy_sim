import cocotb
from cocotb.clock import Clock  # 导入时钟驱动工具
from cocotb.triggers import RisingEdge, Timer
import sys
import random

# 加法器的基本测试

@cocotb.test()
async def test_0(dut):
    
    clock = Clock(dut.clk, 10, unit="ns") 
    cocotb.start_soon(clock.start())
   
    await Timer(1, unit="ns") # 给时钟一点启动时间 
    A = 2
    B = 3
    dut.a.value = A
    dut.b.value = B
    await RisingEdge(dut.clk)
  
    print("Waiting for RisingEdge...")
    # 这里会阻塞，直到 cpp_clock._tick 里的 set_signal_val_int 触发 _check_value_change_callbacks
    print(f"Result q: {dut.q.value}") 
    print(f"Result q_ff: {dut.q_ff.value}")
    assert dut.q.value == A + B