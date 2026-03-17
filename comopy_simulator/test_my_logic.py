import cocotb
from cocotb.triggers import Timer

@cocotb.test()
async def my_first_comopy_test(dut):
    """
    这是你在 CoMoPy 架构上运行的第一个测试用例！
    """
    cocotb.log.info("🚀 恭喜！CoMoPy 成功接管了 cocotb 控制权！")
    
    cocotb.log.info(f"当前 DUT 句柄名称: {dut._name}")
    
    # 模拟等待
    await Timer(10, unit='ns')
    
    cocotb.log.info("✅ 仿真时间流逝了 10ns (在 Python 内存中)。")