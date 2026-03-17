# main.py
import comopy_simulator  # 这行必须在最前面！因为它内部执行了 sys.modules 注入
import os
import sys
import cocotb
from cocotb._init import init_package_from_simulation, run_regression

def start_comopy():
    # 环境设置
    os.environ["COCOTB_TEST_MODULES"] = "test_my_logic"
    os.environ["TOPLEVEL"] = "DUT"
    sys.path.append(os.getcwd())

    print("--- CoMoPy Start ---")
    init_package_from_simulation([])
    print("--- Initialization Complete! ---")
    run_regression([])

if __name__ == "__main__":
    start_comopy()