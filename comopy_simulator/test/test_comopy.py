import cocotb
from cocotb.triggers import Timer

@cocotb.test()
async def test_only_timer(dut):
    print("--- [Test] Start! Waiting for 5ns... ---")
    try:
        print(f"--- [Test] Checking signal: {dut.a} ---")
    except Exception as e:
        print(f"--- [Test] FAILED to access signal: {e} ---")
    
    # 2. 等待 Timer
    await Timer(5, "ns")
    # 核心测试：如果这个 await 能回来，说明注入成功了
    await Timer(5, unit="ns")
    current_time = cocotb.simulator.get_sim_time()
    print(f"--- [Test] Current time: {current_time} ns ---")
    print("--- [Test] Successfully resumed after Timer! ---")

