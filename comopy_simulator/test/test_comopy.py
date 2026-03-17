import cocotb
from cocotb.triggers import Timer

@cocotb.test()
async def test_runner_link(dut):
    dut._log.info("Hello from ComoPy Runner Test!")
    # 将 units 改为 unit
    await Timer(1, unit="ns") 
    dut._log.info("Simulation time advanced successfully!")


import os
import sys


from cocotb_tools.runner import get_runner 

def main():
    runner = get_runner("comopy")

    # 不再手动创建 dut_obj，而是告诉 Runner 文件在哪，类名是什么
    runner.build(
        sources=["my_hdl.py"],  # 替换成包含 SimpleDut 的文件名
        hdl_toplevel="SimpleDut"
    )

    runner.test(
        toplevel="SimpleDut", 
        py_module="test_comopy"
    )

if __name__ == "__main__":
    main()