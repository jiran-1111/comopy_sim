import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

@cocotb.test()
async def test_simplereg(dut):
    """测试 SimpleReg"""
    # 1. 定义时钟
    clock = Clock(dut.clk, 10, unit="ns") # 注意这里是 units (复数)
    
    # 2. 启动时钟
    # 建议保存这个 task 句柄，虽然不是强制的，但更规范
    clk_task = cocotb.start_soon(clock.start())
    
    # 3. 初始化并等待复位（如果有的话）或等待第一个边沿
    dut.d.value = 0
    await RisingEdge(dut.clk)
    
    # 4. 驱动数据
    dut.d.value = 0xAA
    

    await RisingEdge(dut.clk)
    
    await Timer(1, "ns") 
    
    expected_val = 0xAA
    actual_val = int(dut.q.value)
    
    assert actual_val == expected_val, f"Error: Q={actual_val}, Expected={expected_val}"

    await Timer(1, "ns")