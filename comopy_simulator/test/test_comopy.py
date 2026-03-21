import cocotb
from cocotb.triggers import Timer

@cocotb.test()
async def test_only_timer(dut):
    print("--- [Test] Start! Waiting for 5ns... ---")
    try:
        print(f"--- [Test] Checking signal: {dut.a} ---")
    except Exception as e:
        print(f"--- [Test] FAILED to access signal: {e} ---")
    print(f"DEBUG: TYPE of dut.a is {type(dut.a)}")
    print(f"DEBUG: DIR of dut.a is {dir(dut.a)}")
    print(f"DEBUG: dut.a._handle type: {type(dut.a._handle)}")
    print(f"DEBUG: dut.a._set_value function: {dut.a._set_value}")
    A = 5

    dut.a.value = A

    await Timer(2, unit="ns")
    print(f"DEBUG: After drive, dut.a is {dut.a.value}, dut.q is {dut.q.value}")
    assert dut.q.value == A, (
        f"result is incorrect: {dut.q.value} != 5"
    )
    print(f"HARDWARE RAW Q: {dut.q._handle.get_signal_val_long()}")
    assert dut.q._handle.get_signal_val_long() == A


