import os
import sys

# 获取 comopy_simulator 所在的根目录 (test 的上一级)
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 获取根目录的上一级 (即包含 comopy_simulator 文件夹的目录)
parent_dir = os.path.dirname(root_dir)

if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from cocotb_tools.runner import get_runner

def main():
    # 确保当前目录在路径中，以便导入 my_hdl 和 test_comopy
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(curr_dir)

    runner = get_runner("comopy")

    """
    sources 模块文件
    hdl_toplevel 顶层模块的类名
    """
    runner.build(
        sources=["my_hdl.py"],
        hdl_toplevel="SimpleDut"
    )

    # 启动注入并运行 cocotb
    """
    hdl_toplevel 顶层模块的类名
    test_module 测试文件名
    """
    runner.test(
        hdl_toplevel="SimpleDut",      # 对应 GPI 根节点名字
        test_module="test_module"    # 对应 test_comopy.py 文件名
    )

if __name__ == "__main__":
    main()