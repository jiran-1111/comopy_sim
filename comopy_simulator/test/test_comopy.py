import cocotb
from cocotb.triggers import Timer

@cocotb.test()
async def test_1(dut):

    A = 2
    B = 3
    dut.a.value = A
    dut.b.value = B
    await(Timer(10, "ns"))
    assert dut.q.value == A * B , "Security flaw: Output port was successfully overwritten!"


@cocotb.test()
async def test_2(dut):

    A = 1
    B = 4
    dut.a.value = A
    dut.b.value = B
    await(Timer(10, "ns"))
    assert dut.q.value == A * B , "Security flaw: Output port was successfully overwritten!"
