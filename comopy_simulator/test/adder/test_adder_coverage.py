import cocotb
from cocotb.triggers import Timer
# 正确导入！！！这是唯一不报错的写法
from cocotb_coverage.coverage import CoverPoint, CoverCross, coverage_db


# ==============================
# 定义覆盖率采样点
# ==============================
@CoverPoint("adder.a_pos",  xf=lambda a, b, q: a > 0,  bins=[True, False])
@CoverPoint("adder.b_pos",  xf=lambda a, b, q: b > 0,  bins=[True, False])
@CoverPoint("adder.sum_zero", xf=lambda a, b, q: q == 0, bins=[True, False])
@CoverCross("adder.ab_cross", items=["adder.a_pos", "adder.b_pos"])
def sample_adder_coverage(a, b, q):
    pass


# ==============================
# 测试加法器
# ==============================
@cocotb.test()
async def test_adder(dut):
    test_vectors = [
        (0, 0),
        (2, 3),
        (5, 5),
        (10, 20),
        (31, 0),
        (0, 31),
    ]

    for A, B in test_vectors:
        dut.a.value = A
        dut.b.value = B
        await Timer(5, "ns")

        q_actual = dut.q.value.integer
        assert q_actual == A + B, f"Error: {A} + {B} = {q_actual}"

        # 采样覆盖率
        sample_adder_coverage(A, B, q_actual)

    # 打印覆盖率报告
    coverage_db.report_coverage(dut._log.info)