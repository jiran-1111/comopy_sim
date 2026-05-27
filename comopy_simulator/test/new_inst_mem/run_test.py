import sys
from cocotb_tools.runner import get_runner

def main():
    runner = get_runner("comopy")
    runner.build(
        sources=["inst_mem.py"],
        hdl_toplevel="InstMemSync"
    )
    runner.test(
        hdl_toplevel="InstMemSync",
        test_module="test_inst_mem"
    )

if __name__ == "__main__":
    main()