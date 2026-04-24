import os
import sys
import subprocess

def run_task(top_module, test_filename):
    """
    top_module: 硬件顶层名 (SimpleAdder)
    test_filename: 测试文件名 (test_simpleadder)
    """
    python_exe = sys.executable
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    # 测试文件所在的子文件夹路径
    test_dir = os.path.join(curr_dir, "cocotb_test")

    cmd_code = f"""
import sys
import os
# 将根目录和测试目录都加入搜索路径
sys.path.append(r'{curr_dir}')
sys.path.append(r'{test_dir}')

from cocotb_tools.runner import get_runner

runner = get_runner("comopy")
runner.build(sources=["hdl.py"], hdl_toplevel="{top_module}")
runner.test(
    hdl_toplevel="{top_module}",
    test_module="{test_filename}", # 这里直接指定文件名（不带.py）
)
"""
    # 注意：这里不需要 cwd=test_dir，直接在当前目录运行即可
    result = subprocess.run([python_exe, "-c", cmd_code])
    return result.returncode == 0

def main():
    # 配置：顶层模块 -> 对应的测试文件名
    test_configs = [
        #("SimpleAdder", "test_simpleadder"),
        #("Adder", "test_adder"),
        ("Andgate", "test_andgate"),
        #("SimpleReg", "test_simplereg"),
        
        #("Module_shift8", "test_module_shift8"),
        #("Module_add", "test_module_add"),
        ("Reduction", "test_reduction"),
        ("Always_casez", "test_always_casez"),
        #("Module_shift","test_module_shift")

    ]

    results = []

    print(f"\n{'='*40}")
    print("STARTING ALL SIMULATIONS")
    print(f"{'='*40}")

    for top, test_file in test_configs:
        print(f"\n>>> Running Group: {top} using {test_file}.py")
        success = run_task(top, test_file)
        results.append((top, success))

    # --- 汇总 ---
    print("\n" + "="*40)
    print(f"{'TOP MODULE':<20} | {'STATUS':<10}")
    print("-" * 40)
    for top, success in results:
        status = "PASS" if success else "FAILED"
        print(f"{top:<20} | {status:<10}")
    print("="*40)

if __name__ == "__main__":
    main()
