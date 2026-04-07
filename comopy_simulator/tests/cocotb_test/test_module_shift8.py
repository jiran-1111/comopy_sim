import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

@cocotb.test()
async def test_shift8_logic(dut):
    """测试 Module_shift8: 验证不同选择位下的数据延迟"""
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    # 初始状态
    dut.d.value = 0
    dut.sel.value = 0
    await RisingEdge(dut.clk)

    # 发送一个特征值 0xAB
    test_val = 0xAB
    dut.d.value = test_val
    
    # sel=0: 立即输出 (组合逻辑)
    dut.sel.value = 0
    await Timer(1, "ns")
    assert dut.q.value == test_val, "sel=0 应该立即输出 d"

    # 等待一个时钟上升沿，数据进入第一个 DFF
    await RisingEdge(dut.clk)
    dut.d.value = 0x00 # 改变输入，确保输出不是因为输入而维持的
    
    # sel=1: 延迟 1 个周期
    dut.sel.value = 1
    await Timer(1, "ns")
    assert dut.q.value == test_val, "sel=1 应该输出 1 拍后的数据"

    # sel=3: 延迟 3 个周期 (经过 dff0, dff1, dff2)
    await RisingEdge(dut.clk) # 第 2 拍
    await RisingEdge(dut.clk) # 第 3 拍
    dut.sel.value = 3
    await Timer(1, "ns")
    assert dut.q.value == test_val, "sel=3 应该输出 3 拍后的数据"