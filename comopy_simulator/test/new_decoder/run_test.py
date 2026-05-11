import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer
import sys
import random

@cocotb.test()
async def decoder_await_test(dut):
    await Timer(10, "ns")
    await Timer(15, "ns")
    await Timer(5, "ns")

@cocotb.test()
async def decoder_read_write_test(dut):
    for _ in range(10):
        inst = random.randint(0, 0xFFFFFFFF)
        dut.inst.value = inst
        await Timer(2, "ns")

        rd  = (inst >> 7) & 0x1F
        rs1 = (inst >> 15) & 0x1F
        rs2 = (inst >> 20) & 0x1F

        # 只校验模块里真正有的信号！
        assert dut.rd.value == rd, f"rd mismatch: {dut.rd.value} vs {rd}"
        assert dut.rs1.value == rs1, f"rs1 mismatch"
        assert dut.rs2.value == rs2, f"rs2 mismatch"

@cocotb.test()
async def decoder_edge_test(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    for _ in range(10):
        inst = random.randint(0, 0xFFFFFFFF)
        dut.inst.value = inst

        await RisingEdge(dut.clk)
        await FallingEdge(dut.clk)
        await Timer(2, "ns")

        rd  = (inst >> 7) & 0x1F
        rs1 = (inst >> 15) & 0x1F
        rs2 = (inst >> 20) & 0x1F

        assert dut.rd.value == rd
        assert dut.rs1.value == rs1
        assert dut.rs2.value == rs2

import os
import sys
from cocotb_tools.runner import get_runner

def main():
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(curr_dir)

    runner = get_runner("comopy")

    runner.build(
        sources=["decoder.py"],
        hdl_toplevel="Decoder"
    )

    runner.test(
        hdl_toplevel="Decoder",
        test_module="run_test"
    )

if __name__ == "__main__":
    main()