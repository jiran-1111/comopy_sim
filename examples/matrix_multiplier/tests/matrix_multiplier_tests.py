# This file is public domain, it can be freely copied without restrictions.
# SPDX-License-Identifier: CC0-1.0
from __future__ import annotations

import logging
import math
import os
import random
from collections import deque
from collections.abc import Sequence
from typing import (
    Any,
    Callable,
    Generic,
    Protocol,
    TypeVar,
)

import cocotb
from cocotb.clock import Clock
from cocotb.handle import LogicObject, ValueObjectBase
from cocotb.task import Task
from cocotb.triggers import Event, FallingEdge, ReadOnly, RisingEdge, Trigger
from cocotb.types import Array, LogicArray, Range

T = TypeVar("T")


# 仿真中的事务缓冲区
class Mailbox(Generic[T]):
    """A deque with signals for use in testbench components."""

    def __init__(self) -> None:
        # 双端队列存数据
        self._queue: deque[T] = deque()
        self._event = Event()

    # 往信箱里放数据
    def put(self, item: T) -> None:
        """Put an item in the mailbox."""
        self._queue.append(item)
        self._event.set()

    # 取数据
    def get(self) -> T:
        """Get an item from the mailbox."""
        if self._queue:
            return self._queue.popleft()
        else:
            raise RuntimeError("Mailbox is empty")

    # 等待信箱里有数据
    def wait(self) -> Trigger:
        """Wait for an item to be put in the mailbox."""
        if not self._queue:
            self._event.clear()
        return self._event.wait()

    # 判断是否为空
    def empty(self) -> bool:
        """Check if the mailbox is empty."""
        return not self._queue


# 监视接口
# 监视input output
class DataValidMonitor(Generic[T]):
    """Reusable Monitor of data/valid streaming interface.

    Assumes *rst*, *valid*, and *datas* registered signals on rising edge of *clk*.
    Glitches will cause incorrect values to be recorded.
    Assumes *valid* is active at `1`, and *rst* is active at `!0`.
    Assumes *valid* and *rst* cannot have weak values.

    Args:
        clk: clock signal
        rst: reset signal
        valid: control signal noting a transaction occurred
        datas: named handles to be sampled when transaction occurs
    """

    def __init__(
        self,
        name: str,
        clk: LogicObject,
        rst: LogicObject,
        datas: dict[str, ValueObjectBase[T, Any]],
        valid: LogicObject,
    ) -> None:
        self.name = name
        self.log = logging.getLogger(name)
        self._clk = clk
        self._rst = rst
        self._datas = datas
        self._valid = valid
        self._callbacks: list[Callable[[dict[str, T]], Any]] = []
        self._task: Task[None] | None = None

    # 连接golden model
    def add_callback(self, callback: Callable[[dict], Any]) -> None:
        """Add callback to be called with transaction data when a transaction is observed."""
        self._callbacks.append(callback)

    def start(self) -> None:
        """Start monitor."""
        if self._task is not None:
            raise RuntimeError("Monitor already started")
        self._task = cocotb.start_soon(self._run())

    def stop(self) -> None:
        """Stop monitor."""
        if self._task is None:
            raise RuntimeError("Monitor never started")
        self._task.cancel()
        self._task = None

    async def _run(self) -> None:
        while True:
            # 等时钟上升沿 只读
            await RisingEdge(self._clk)
            await ReadOnly()
            # 处于reset 不采样
            if self._rst.value != "0":
                self.log.debug("Waiting for reset to finish...")
                await FallingEdge(self._rst)
                self.log.debug("Reset finished")
                continue
            elif self._valid.value != "1":
                await RisingEdge(self._valid)
                await ReadOnly()
                # Fallthrough and sample data since we assume valid is registered.

            # send sample to all registered callbacks
            # _sample函数采样数据
            transaction = self._sample()
            self.log.debug("Observed: %r", transaction)
            for cb in self._callbacks:
                cb(transaction)
    # 采样数据的函数
    def _sample(self) -> dict[str, T]:
        """Samples the data signals and builds a transaction object."""
        return {name: handle.value for name, handle in self._datas.items()}

# 驱动接口(driver)
class DataValidDriver(Generic[T]):
    """Reusable Driver of data/valid streaming interface."""
    # 按 data/valid 协议驱动 DUT 输入
    def __init__(
        self,
        name: str,
        clk: LogicObject,
        rst: LogicObject,
        datas: dict[str, ValueObjectBase[Any, T]],
        valid: LogicObject,
        initial_values: dict[str, T] | None = None,
    ) -> None:
        self.name = name
        self.log = logging.getLogger(name)
        self._clk = clk
        self._rst = rst
        self._datas = datas
        self._valid = valid
        self._initial_values = initial_values
        self._task: Task[None] | None = None
        self._mb = Mailbox[tuple[dict[str, T], Event]]()

    # 先把数据存起来
    def send(self, data: dict[str, T]) -> Trigger:
        """Send data to driver.

        Args:
            data: Data to be applied to the interface.

        Returns
            A Trigger which will fire after the data is applied to the interface.
        """
        e = Event()
        self.log.debug("Queued: %r", data)
        # 放入信箱
        self._mb.put((data, e))
        return e.wait()

    def start(self) -> None:
        """Start driver."""
        if self._task is not None:
            raise RuntimeError("Driver already started")
        self._task = cocotb.start_soon(self._run())

    def stop(self) -> None:
        """Stop driver."""
        if self._task is None:
            raise RuntimeError("Driver never started")
        self._task.cancel()
        self._task = None

    # 真正送数据的函数
    async def _run(self) -> None:
        while True:
            await RisingEdge(self._clk)
            self._valid.value = 0

            # 如果reset了 就复位
            if self._rst.value != "0":
                self.log.debug("Resetting...")
                # drive reset values
                if self._initial_values is not None:
                    for name, handle in self._datas.items():
                        if name in self._initial_values:
                            handle.value = self._initial_values[name]
                # wait for reset to finish
                await FallingEdge(self._rst)
                self.log.debug("Finished reset")
                continue

            # 如果没reset 但邮箱是空的 等
            elif self._mb.empty():
                self.log.debug("Waiting for input")
                await self._mb.wait()
                continue

            self._valid.value = 1
            # 从邮箱取出要送DUT的数据
            data, e = self._mb.get()
            self._apply(data)
            self.log.debug("Applied: %r", data)
            e.set()

    def _apply(self, data: dict[str, T]) -> None:
        """Apply data to the interface."""
        for name, handle in self._datas.items():
            handle.value = data[name]

# 参考模型（golden model)
class MatrixMultiplierModel:
    """Transaction-level model of a matrix multiplier."""

    # 矩阵行数 列数 位宽 来自dut的parameter
    def __init__(
        self,
        name: str,
        A_ROWS: int,
        A_COLUMNS_B_ROWS: int,
        B_COLUMNS: int,
        DATA_WIDTH: int,
    ) -> None:
        self.name = name
        self.log = logging.getLogger(name)
        self.A_ROWS = A_ROWS
        self.A_COLUMNS_B_ROWS = A_COLUMNS_B_ROWS
        self.B_COLUMNS = B_COLUMNS
        self.DATA_WIDTH = DATA_WIDTH

        self._OUTPUT_RANGE = Range(
            (DATA_WIDTH * 2) + math.ceil(math.log2(A_COLUMNS_B_ROWS)) - 1,
            "downto",
            0,
        )

        self._output_callbacks: list[Callable[[list[LogicArray]], None]] = []

    # 连接checker model算出结果就告诉checker期望值
    def add_output_callback(self, callback: Callable[[list[LogicArray]], None]) -> None:
        """Add callback to be called with output data when a transaction is produced."""
        self._output_callbacks.append(callback)

    
    def send_input(
        self, a_matrix: Array[LogicArray], b_matrix: Array[LogicArray]
    ) -> None:
        """Send data to the output and evaluate the model."""
        self.log.debug("Received input:\n  A: %r\n  B: %r", a_matrix, b_matrix)

        # 矩阵乘法
        result = [
            LogicArray(
                sum(
                    a_matrix[(i * self.A_COLUMNS_B_ROWS) + n].to_unsigned()
                    * b_matrix[(n * self.B_COLUMNS) + j].to_unsigned()
                    for n in range(self.A_COLUMNS_B_ROWS)
                ),
                self._OUTPUT_RANGE,
            )
            for i in range(self.A_ROWS)
            for j in range(self.B_COLUMNS)
        ]

        self.log.debug("Sending output: %r", result)
        for cb in self._output_callbacks:
            cb(result)


T_contra = TypeVar("T_contra", contravariant=True)


class CompareFunc(Protocol[T_contra]):
    """Type for a function that compares two values of the same type.

    *expected* and *actual* are passed as keyword arguments.
    """

    def __call__(self, *, expected: T_contra, actual: T_contra) -> bool:
        pass

# 把期望结果和实际结果对比 等价与UVM scoreboard
class InOrderChecker(Generic[T]):
    # 使用队列保存参考模型产生的期望结果 当dut输出实际结果时 按fifo顺序进行一一比较
    """Checker of expected vs actual results.

    Checks results in order of arrival.
    Expects *expected* data to arrive before *actual* data.
    If *actual* data arrives before *expected* data, an error is recorded.
    """

    def __init__(
        self,
        name: str,
        fail_on_error: bool = True,
        cmp: CompareFunc = lambda expected, actual: expected == actual,
    ) -> None:
        self.name = name
        self.log = logging.getLogger(name)
        self._fail_on_error = fail_on_error
        self._cmp = cmp
        self._expected_queue: deque[T] = deque()
        self.errors: int = 0
    
    # 将期望结果排进队列
    def addExpected(self, expected: T) -> None:
        """Add expected data to the checker."""
        self.log.debug("Added expected: %r", expected)
        self._expected_queue.append(expected)

    # DUT输出结果送到checker
    def addActual(self, actual: T) -> None:
        """Add actual data to the checker."""
        self.log.debug("Added actual: %r", actual)
        # 如果没有期望值就报错
        if not self._expected_queue:
            raise RuntimeError("Unexpected actual data received")
        
        expected = self._expected_queue.popleft()

        if self._fail_on_error:
            assert self._cmp(expected=expected, actual=actual)
        elif not self._cmp(expected=expected, actual=actual):
            self.log.error("MISMATCH!\n  Expected: %r\n  Actual: %r", expected, actual)
            self.errors += 1

        # 匹配成功
        else:
            self.log.debug("Matched:\n  Expected: %r\n  Actual: %r", expected, actual)


# 顶层验证环境（Env)
class MatrixMultiplierTestbench:
    """
    Reusable checker of a matrix_multiplier instance

    Args:
        matrix_multiplier_entity: handle to an instance of matrix_multiplier
    """

    def __init__(self, dut: Any, name: str | None = None) -> None:
        self.dut = dut
        self.name = name if name is not None else type(self).__qualname__
        self.log = logging.getLogger(self.name)
        self.log.setLevel(logging.INFO)

        # 从DUT获取参数 parameters
        self.A_ROWS = int(self.dut.A_ROWS.value)
        self.A_COLUMNS_B_ROWS = int(self.dut.A_COLUMNS_B_ROWS.value)
        self.B_COLUMNS = int(self.dut.B_COLUMNS.value)
        self.DATA_WIDTH = int(self.dut.DATA_WIDTH.value)
        # 创建时钟
        self.clk_drv = Clock(self.dut.clk_i, 10, unit="ns")

        # 输入driver 
        self.input_drv = DataValidDriver(
            name=f"{self.name}.input_drv",
            clk=self.dut.clk_i,
            rst=self.dut.reset_i,
            valid=self.dut.valid_i,
            datas={"A": self.dut.a_i, "B": self.dut.b_i},
            initial_values={
                "A": self.create_a_matrix(lambda: 0),
                "B": self.create_b_matrix(lambda: 0),
            },
        )

        # 创建输入monitor 送给参考模型
        self.input_mon = DataValidMonitor(
            name=f"{self.name}.input_mon",
            clk=self.dut.clk_i,
            rst=self.dut.reset_i,
            valid=self.dut.valid_i,
            datas={"A": self.dut.a_i, "B": self.dut.b_i},
        )

        # 输出monitor 送给checker
        self.output_mon = DataValidMonitor(
            name=f"{self.name}.output_mon",
            clk=self.dut.clk_i,
            rst=self.dut.reset_i,
            valid=self.dut.valid_o,
            datas={"C": self.dut.c_o},
        )

        # 创建参考模型  
        self.model = MatrixMultiplierModel(
            name=f"{self.name}.model",
            A_ROWS=self.A_ROWS,
            A_COLUMNS_B_ROWS=self.A_COLUMNS_B_ROWS,
            B_COLUMNS=self.B_COLUMNS,
            DATA_WIDTH=self.DATA_WIDTH,
        )

        # 创建checker用于对比
        self.checker = InOrderChecker[Sequence[LogicArray]](
            name=f"{self.name}.checker",
        )

        # connect monitors to model and checker
        
        self.input_mon.add_callback(
            lambda datas: self.model.send_input(
                a_matrix=datas["A"], b_matrix=datas["B"]
            )
        )
        # 参考模型连接到checker
        self.model.add_output_callback(self.checker.addExpected)
        # output monitor 连接到checker
        self.output_mon.add_callback(lambda datas: self.checker.addActual(datas["C"]))

    # 将python的矩阵形式转换成DUT需要的一维向量
    def create_a_matrix(self, func: Callable[[], int]) -> list[LogicArray]:
        """Create a matrix of the size of input A.

        Takes a function to generate values.
        Literal values can be used by passing `lambda: {value}`.
        """
        return [

            LogicArray(func(), self.DATA_WIDTH)
            for _ in range(self.A_ROWS * self.A_COLUMNS_B_ROWS)
        ]

    def create_b_matrix(self, func: Callable[[], int]) -> list[LogicArray]:
        """Create a matrix of the size of input B.

        Takes a function to generate values.
        Literal values can be used by passing `lambda: {value}`.
        """
        return [
            LogicArray(func(), self.DATA_WIDTH)
            for _ in range(self.A_COLUMNS_B_ROWS * self.B_COLUMNS)
        ]

    # 控制函数：启动 停止 复位
    def start(self) -> None:
        """Starts sub-components."""
        self.clk_drv.start()
        self.input_drv.start()
        self.input_mon.start()
        self.output_mon.start()

    def stop(self) -> None:
        """Stops sub-components."""
        self.clk_drv.stop()
        self.input_drv.stop()
        self.input_mon.stop()
        self.output_mon.stop()

    async def reset(self, cycles: int = 3) -> None:
        """Reset the design under test."""
        self.dut.reset_i.value = 1
        for _ in range(cycles):
            await RisingEdge(self.dut.clk_i)
        self.dut.reset_i.value = 0

# cocotb test
@cocotb.test()
async def test_random(dut: Any) -> None:
    """Test matrix multiplier with random data."""

    # Create the testbench, start it and go through reset
    # 创建测试系统并启动 乘法器进入复位状态
    tb = MatrixMultiplierTestbench(dut)
    tb.start()
    await tb.reset()

    # Run design with random data and gaps
    # 循环3000次 随机生成两个矩阵A B
    NUM_SAMPLES = int(os.environ.get("NUM_SAMPLES", "3000"))
    for i in range(NUM_SAMPLES):
        # Send random data to the driver
        # 随机生成矩阵A B 并发送给DUT
        tb.input_drv.send(
            {
                "A": tb.create_a_matrix(lambda: random.getrandbits(tb.DATA_WIDTH)),
                "B": tb.create_b_matrix(lambda: random.getrandbits(tb.DATA_WIDTH)),
            }
        )

        # Wait random clock cycles before sending another
        await tb.clk_drv.cycles(random.randint(1, 5))

        # Log progress
        # 每100次循环进行打印
        if i % 100 == 0:
            tb.log.info("%d / %d", i, NUM_SAMPLES)

    # Wait for all transactions to be processed and stop the testbench
    await tb.clk_drv.cycles(5)
    tb.stop()

    # Check for errors if the checkers weren't set to fail on error
    assert tb.checker.errors == 0
