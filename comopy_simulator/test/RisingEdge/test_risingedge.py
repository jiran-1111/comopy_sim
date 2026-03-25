import cocotb
from cocotb.clock import Clock  # 导入时钟驱动工具
from cocotb.triggers import RisingEdge, Timer
import sys
import random

@cocotb.test()
async def test_0(dut):
    
    clock = Clock(dut.clk, 10, unit="ns") 
    cocotb.start_soon(clock.start())
    await Timer(1, unit="ns") # 给时钟一点启动时间
    A = 2
    B = 3
    dut.a.value = A
    dut.b.value = B
    
    print("Waiting for RisingEdge...")
    # 这里会阻塞，直到 cpp_clock._tick 里的 set_signal_val_int 触发 _check_value_change_callbacks
    await RisingEdge(dut.clk) 
    print(f"GOT EDGE! Result: {dut.q.value}")
    assert dut.q.value == A + B

# 加法器的基本测试
@cocotb.test()
async def test_1(dut):

    A = 1
    B = 4
    dut.a.value = A
    dut.b.value = B
    await(Timer(10, "ns"))
    assert dut.q.value == A + B , "Security flaw: Output port was successfully overwritten!"
    
@cocotb.test()
async def test_2(dut):

    A = 3
    B = 2
    dut.a.value = A
    dut.b.value = B
    await(Timer(5, "ns"))
    assert dut.q.value == A + B , "Security flaw: Output port was successfully overwritten!"


@cocotb.test()
async def test_3(dut):

    A = 5
    B = 10

    dut.a.value = A
    dut.b.value = B

    await Timer(2, unit="ns")

    assert dut.q.value == A + B, (
        f"Adder result is incorrect: {dut.q.value} != 15"
    )


# 随机测试
@cocotb.test()
async def test_4(dut):

    for _ in range(10):
        # 随机抽取0~15的整数
        A = random.randint(0, 15)
        B = random.randint(0, 15)

        dut.a.value = A
        dut.b.value = B

        await Timer(2, unit="ns")

        # 输出和python的正确模型相匹配        
        assert dut.q.value == A + B, (
            f"Randomised test failed with: {dut.a.value} + {dut.b.value} = {dut.q.value}"
        )
