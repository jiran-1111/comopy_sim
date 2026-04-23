# This file is public domain, it can be freely copied without restrictions.
# SPDX-License-Identifier: CC0-1.0
# Simple tests for an adder module
from __future__ import annotations

import os
import random
import sys
from pathlib import Path

import cocotb
from cocotb.triggers import Timer
from cocotb_tools.runner import get_runner

# 只有仿真已经启动时才import 因为有可能pytest启动时还没仿真 cocotb测试运行在仿真器进程里
if cocotb.simulator.is_running():
    from adder_model import adder_model

import cocotb
from cocotb.clock import Clock  # 导入时钟驱动工具
from cocotb.triggers import RisingEdge,FallingEdge, Timer
import sys
import random

@cocotb.test()
async def adder_read_write__test(dut):

 
    await Timer(10, "ns")
    await Timer(15, "ns")
    await Timer(5, "ns")
       

@cocotb.test()
async def adder_await_test(dut):

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
        await Timer(1, "ns")
        await FallingEdge(dut.clk)
        await Timer(2, "ns")
    
        # 输出和python的正确模型相匹配        
        assert dut.q.value == A + B, (
            f"Randomised test failed with: {dut.a.value} + {dut.b.value} = {dut.q.value}"
        )
"""   
# 加法器的基本测试
@cocotb.test()
async def adder_basic_test(dut):
   

    A = 5
    B = 10

    dut.A.value = A
    dut.B.value = B

    await Timer(2, unit="ns")

    assert dut.X.value == adder_model(A, B), (
        f"Adder result is incorrect: {dut.X.value} != 15"
    )


# 随机测试
@cocotb.test()
async def adder_randomised_test(dut):
   
    for _ in range(10):
        # 随机抽取0~15的整数
        A = random.randint(0, 15)
        B = random.randint(0, 15)

        dut.A.value = A
        dut.B.value = B

        await Timer(2, unit="ns")

        # 输出和python的正确模型相匹配        
        assert dut.X.value == adder_model(A, B), (
            f"Randomised test failed with: {dut.A.value} + {dut.B.value} = {dut.X.value}"
        )
"""
# pytest入口 启动仿真
def test_adder_runner():
    """Simulate the adder example using the Python runner.

    This file can be run directly or via pytest discovery.
    """
    hdl_toplevel_lang = os.getenv("HDL_TOPLEVEL_LANG", "verilog")  # 默认verilog
    sim = os.getenv("SIM", "icarus")  # 仿真器默认icarus

    # 得到整个项目的根目录adder
    proj_path = Path(__file__).resolve().parent.parent
    # equivalent to setting the PYTHONPATH environment variable
    sys.path.append(str(proj_path / "model"))

    if hdl_toplevel_lang == "verilog":
        sources = [proj_path / "hdl" / "new_adder.sv"] #待编译的源文件


    build_test_args = []
    if hdl_toplevel_lang == "vhdl" and sim == "xcelium":
        build_test_args = ["-v93"]

    # equivalent to setting the PYTHONPATH environment variable
    sys.path.append(str(proj_path / "tests"))

    runner = get_runner(sim) # 用刚才选择仿真器得到runner对象
    runner.build(  # 编译
        sources=sources,
        hdl_toplevel="adder",
        always=True,
        build_args=build_test_args,
    )
    runner.test(
        # hdl_toplevel 指定顶层模块
        # test_module 在这个模块找到所有@cocotb.test()并依次执行
        hdl_toplevel="adder", test_module="test_adder", test_args=build_test_args
    )


if __name__ == "__main__":
    test_adder_runner()
