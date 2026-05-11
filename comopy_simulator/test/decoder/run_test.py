import os
import sys
from cocotb_tools.runner import get_runner

def main():
    
    runner = get_runner("comopy")

    runner.build(
        sources=["decoder.py"],
        hdl_toplevel="Decoder"
    )

    runner.test(
        hdl_toplevel="Decoder",
        test_module="test_decoder"
    )

if __name__ == "__main__":
    main()