import os
import sys
from pathlib import Path
from cocotb_tools.runner import get_runner

def run_icarus_task(top_module, test_module):
    """
    使用 Icarus Verilog 运行单个测试任务
    """
    curr_dir = Path(__name__).parent.resolve()
    # 1. 指定 Verilog 源代码路径
    sources = [curr_dir / "design.sv"] 
    
    # 2. 将测试脚本所在目录加入系统路径
    test_dir = curr_dir / "cocotb_test"
    sys.path.append(str(test_dir))

    # 3. 获取 Icarus Runner
    sim = "icarus"
    runner = get_runner(sim)

    print(f"\n--- Building and Testing Top: {top_module} ---")
    
    # 4. 编译阶段
    runner.build(
        sources=sources,
        hdl_toplevel=top_module,
        always=True, # 强制重新编译
    )

    # 5. 测试阶段
    runner.test(
        hdl_toplevel=top_module,
        test_module=test_module, # 不带 .py 后缀
    )

def main():
    # 配置列表：(Verilog顶层模块名, Cocotb测试文件名)
    test_configs = [
        ("Andgate", "test_andgate"),
        ("SimpleAdder", "test_simpleadder"),
        ("Module_add", "test_module_add"),
        ("Reduction", "test_reduction"),
        ("Always_casez", "test_always_casez"),
        ("SimpleReg", "test_simplereg"),
        ("Adder", "test_adder"),
        ("Module_shift8", "test_module_shift8"),
        ("Module_shift","test_module_shift")
    ]

    for top, test_file in test_configs:
        try:
            run_icarus_task(top, test_file)
        except Exception as e:
            print(f"Error running {top}: {e}")

if __name__ == "__main__":
    main()