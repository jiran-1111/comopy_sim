import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer
import sys
import random


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
        test_module="new_test"
    )

if __name__ == "__main__":
    main()