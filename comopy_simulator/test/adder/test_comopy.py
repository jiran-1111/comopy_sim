
import cocotb
from cocotb.clock import Clock  # 导入时钟驱动工具
from cocotb.triggers import RisingEdge, Timer
import sys
import random

# 加法器的基本测试
@cocotb.test()
async def test_0(dut):

    A = 1
    B = 4
    dut.a.value = A
    await Timer(1, "ps")
    #dut.b.value = B
    dut.b._handle.set_signal_val_int(0, 4)
    
    dut._log.info(f"Internal data of A: {dut.a._handle.obj._data}")
    dut._log.info(f"Internal data of B: {dut.b._handle.obj._data}")
    
    await(Timer(10, "ns"))
    assert dut.q.value == A + B , "Security flaw: Output port was successfully overwritten!"



@cocotb.test()
async def test_1(dut):

    A = 2
    B = 3
    dut.a.value = A
    dut.b.value = B
    await(Timer(5, "ns"))
    assert dut.q.value == A + B , "Security flaw: Output port was successfully overwritten!"




# 加法器的基本测试
@cocotb.test()
async def adder_basic_test(dut):

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


import cocotb
from cocotb.triggers import Timer
import random

@cocotb.test()
async def adder_randomised_test(dut):
    """自主实现覆盖率统计的随机测试"""
    
    # --- 1. 初始化统计字典 (Bins) ---
    # 模拟 a, b 的 0-15 范围
    bins_a = {i: 0 for i in range(16)}
    bins_b = {i: 0 for i in range(16)}
    # 模拟 cross (a, b) 的 256 种组合
    bins_cross = {(a, b): 0 for a in range(16) for b in range(16)}

    dut._log.info("Starting randomised test with custom monitor...")

    # 运行 300 次以获得更好的覆盖分布
    for i in range(2000):
        A = random.randint(0, 15)
        B = random.randint(0, 15)

        dut.a.value = A
        dut.b.value = B

        await Timer(2, unit="ns")
        
        # --- 2. 实时采样 ---
        bins_a[A] += 1
        bins_b[B] += 1
        bins_cross[(A, B)] += 1

        # 结果校验
        assert dut.q.value == A + B, f"Error at {A}+{B}"

    # --- 3. 计算并打印报告 ---
    def get_cov(bins):
        covered = sum(1 for count in bins.values() if count > 0)
        total = len(bins)
        return covered, total, (covered / total) * 100

    dut._log.info("="*50)
    dut._log.info("      COMOPY NATIVE COVERAGE REPORT")
    dut._log.info("="*50)

    for name, b in [("Input A", bins_a), ("Input B", bins_b), ("Cross A&B", bins_cross)]:
        cv, total, per = get_cov(b)
        dut._log.info(f"-> {name:10}: {cv}/{total} bins ({per:.2f}%)")
    
    dut._log.info("="*50)
    dut._log.info("Simulation Finished Successfully!")