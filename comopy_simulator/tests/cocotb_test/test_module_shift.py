import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

@cocotb.test()
async def test_shift_pipeline(dut):
    """测试移位寄存器：验证数据在流水线中的逐拍传递"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    
    # 输入一个标记数据 0x1
    dut.d.value = 1
    await RisingEdge(dut.clk)
    dut.d.value = 0 # 随后撤销输入
    
    # 第一拍：数据应到达 dff0.q (信号 a)
    await Timer(1, "ns")
    assert dut.a.value == 1, "Data should be at stage A"
    assert dut.q.value == 0, "Data should NOT reach final output yet"
    
    # 第二拍：数据应从 a 移动到 b
    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.a.value == 0
    assert dut.b.value == 1, "Data should be at stage B"
    
    # 第三拍：数据最终到达输出 q
    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.b.value == 0
    assert dut.q.value == 1, "Data should reach final Output Q"