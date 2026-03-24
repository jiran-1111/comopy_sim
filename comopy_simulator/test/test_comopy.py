import cocotb
from cocotb.triggers import Timer
import random
@cocotb.test()
async def test_1(dut):

    A = 2
    B = 3
    dut.a.value = A
    dut.b.value = B
    await(Timer(5, "ns"))
    assert dut.q.value == A + B , "Security flaw: Output port was successfully overwritten!"


@cocotb.test()
async def test_2(dut):

    A = 1
    B = 4
    dut.a.value = A
    dut.b.value = B
    await(Timer(10, "ns"))
    assert dut.q.value == A + B , "Security flaw: Output port was successfully overwritten!"


# 加法器的基本测试
@cocotb.test()
async def adder_basic_test(dut):
    """Test for 5 + 10"""

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
async def adder_randomised_test(dut):
    """Test for adding 2 random numbers multiple times"""

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