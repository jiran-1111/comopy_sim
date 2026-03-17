from __future__ import annotations
import sys
import os
import threading
from types import ModuleType
from typing import Callable,Any,TYPE_CHECKING

# 接口标准见 src/cocotb/simulator.pyi
# c++实现接口见 src/cocotb/share/lib/pygpi/bind.cpp

# 静态检查时导入，运行时不导入，完美避开循环依赖
if TYPE_CHECKING:
    from cocotb.handle import GPIDiscovery
    from logging import Logger
else:
    GPIDiscovery = Any
    Logger = Any
# === 1. 定义所有simulator.pyi要求定义的类  ===

class cpp_clock:
    """C++ 时钟加速器类。
    当 impl="gpi" 时，cocotb 会使用此类来绕过 Python 协程直接在 C++ 层翻转信号。
    """
    def __init__(self, signal: 'gpi_sim_hdl') -> None:
        self.signal = signal
    def start(self, period_steps: int, high_steps: int, start_high: bool, set_action: int) -> None:
        # 实现逻辑：启动一个后台线程或定时器，按照周期不断调用 signal.set_signal_val_int
        pass
    def stop(self) -> None:
        # 实现逻辑：停止定时器
        pass

# 23
class gpi_sim_hdl:
    """对应 C++ 中的 GpiObjHdl 类。代表仿真器中的一个硬件对象（Module, Net, Reg 等）。"""
    def __init__(self, name: str = "top"):
        self.name = name
        self.hdl = self  # 必须存在，以兼容 clock_create 的入参访问

    def get_const(self) -> bool: 
        """返回该信号是否为常量（如 Verilog 中的 parameter 或 localparam）。"""
        return False

    def get_definition_file(self) -> str: 
        """返回定义该对象的源码文件路径。"""
        return "virtual.v"

    def get_definition_name(self) -> str: 
        """返回该对象的类型定义名（如模块名）。"""
        return "logic"

    def get_handle_by_index(self, index: int) -> 'gpi_sim_hdl | None': 
        """如果该对象是数组或向量，通过索引获取成员句柄。"""
        return None

    def get_handle_by_name(
        self, name: str, discovery_method: "GPIDiscovery" = 0
    ) -> 'gpi_sim_hdl' | None: 
        """获取当前层级下指定名称的句柄。"""
        return gpi_sim_hdl(f"{self.name}.{name}")

    def get_indexable(self) -> bool: 
        """返回该对象是否可以被索引（是否为数组/向量）。"""
        return False

    def get_name_string(self) -> str: 
        """返回对象的完整路径名。"""
        return self.name

    def get_num_elems(self) -> int: 
        """如果是数组，返回元素个数；如果是向量，返回位宽。"""
        return 0

    def get_range(self) -> tuple[int, int, int]: 
        """返回数组或向量的范围 (left, right, direction)。"""
        return (0, 0, 0)

    def get_signal_val_binstr(self) -> str: 
        """以字符串形式返回二进制值（支持 'x', 'z', 'u', 'w'）。"""
        return "0"

    def get_signal_val_long(self) -> int: 
        """将信号值作为 64 位整数返回。"""
        return 0

    def get_signal_val_real(self) -> float: 
        """将信号值作为浮点数返回。"""
        return 0.0

    def get_signal_val_str(self) -> bytes: 
        """将信号值作为字符串（ASCII）返回。"""
        return b""

    def get_type(self) -> int:
        """返回对象的 GPI 类型（对应常量表中的数值）。"""
        return 2 # 默认为 MODULE

    def get_type_string(self) -> str: 
        """返回类型的字符串表示（如 "MODULE", "LOGIC"）。"""
        return "MODULE"

    def iterate(self, mode: int) -> 'gpi_iterator_hdl':
        """返回一个迭代器，用于遍历该对象下的子对象。"""
        return gpi_iterator_hdl()

    def set_signal_val_binstr(self, action: int, value: str) -> None: 
        """使用二进制字符串设置信号值。"""
        pass

    def set_signal_val_int(self, action: int, value: int) -> None: 
        """使用整数设置信号值。action 对应 Deposit/Force 等。"""
        pass

    def set_signal_val_real(self, action: int, value: float) -> None: 
        """使用浮点数设置信号值。"""
        pass

    def set_signal_val_str(self, action: int, value: bytes) -> None: 
        """使用字节序列设置信号值。"""
        pass

    def __eq__(self, other: object) -> bool:
        return isinstance(other, gpi_sim_hdl) and self.name == other.name

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self.name)
# 4
class gpi_cb_hdl: 
    """对应 C++ 中的 GpiCbHdl 类。代表一个已注册的回调（如 Timer, Edge）。"""
    def deregister(self): 
        """取消已注册的回调，使其不再触发。"""
        pass
    def __eq__(self, other: object) -> bool: return self is other
    def __ne__(self, other: object) -> bool: return not self.__eq__(other)
    def __hash__(self) -> int: return id(self)

# 5
class gpi_iterator_hdl: 
    """对应 C++ 中的 GpiIteratorHdl 类。用于遍历层级。"""
    def __eq__(self, other: object) -> bool: return self is other
    def __ne__(self, other: object) -> bool: return not self.__eq__(other)
    def __hash__(self) -> int: return id(self)
    def __iter__(self) : return self
    def __next__(self) -> gpi_sim_hdl: 
        raise StopIteration

# === 2. 创建模拟模块并注入常量 ===

# 这里创建一个python模块对象做simulator
sim = ModuleType("cocotb.simulator")

# 常量注入：将gpi接口定义的数值手动注入到sim模块中
# src/cocotb/share/include/gpi.h
constants = {
    "DRIVERS": 2,
    "ENUM": 7,
    "GENARRAY": 12,
    "INTEGER": 10,
    "LOADS": 3,
    "LOGIC": 15,
    "LOGIC_ARRAY": 16,
    "MEMORY": 1,
    "MODULE": 2,
    "NETARRAY": 10,
    "OBJECTS": 1,
    "PACKAGE": 13,
    "REAL": 9,
    "STRING": 11,
    "STRUCTURE": 8,
    "PACKED_STRUCTURE": 14,
    "UNKNOWN": 0,
    "RISING": 0,
    "FALLING": 1,
    "VALUE_CHANGE": 2,
    "RANGE_UP": 1,
    "RANGE_DOWN": -1,
    "RANGE_NO_DIR": 0,
}

for name, val in constants.items():
    setattr(sim, name, val)


# === 3. 定义函数接口 17 个 ===
def get_precision() -> int: 
    """返回仿真器的时间精度（以 10 的幂表示，如 -12 代表 ps）。"""
    return -9

def get_root_handle(name: str | None) -> gpi_sim_hdl | None: 
    print(f"--- [DEBUG] Cocotb requested root handle for: {name} ---")
    return gpi_sim_hdl(name if name else "top")

def get_sim_time() -> tuple[int, int]: 
    """返回当前仿真时间，以 (高32位, 低32位) 的整数元组返回。"""
    return 0, 0

def get_simulator_product() -> str: 
    """返回仿真器产品名称。"""
    return "CoMoPy"

def get_simulator_version() -> str: 
    """返回仿真器版本号。"""
    return "1.0"

def is_running() -> bool: 
    """返回仿真器当前是否正在运行。"""
    return True

def set_gpi_log_level(level: int) -> None: 
    """设置 C 层 GPI 的日志等级。"""
    pass

def package_iterate() -> gpi_iterator_hdl: 
    """用于在 VHDL 等支持 package 的语言中遍历包内容。"""
    return gpi_iterator_hdl()

def register_nextstep_callback(func: Callable[..., Any], *args: Any) -> gpi_cb_hdl: 
    """注册一个在当前时间步（Time step）所有事件处理完后触发的回调。"""
    return gpi_cb_hdl()

def register_readonly_callback(func: Callable[..., Any], *args: Any) -> gpi_cb_hdl: 
    """注册一个在 Read-Only 阶段触发的回调，此时不能修改信号值。"""
    return gpi_cb_hdl()

def register_rwsynch_callback(func: Callable[..., Any], *args: Any) -> gpi_cb_hdl:
    """注册一个同步回调，通常用于准备写操作。"""
    return gpi_cb_hdl()

def register_timed_callback(time_steps, callback, *args):
    handle = gpi_cb_hdl()
    # 模拟仿真时间推进：启动一个线程在 10ms 后叫醒 Cocotb
    # 注意：这里的 callback 必须被调用，否则测试会永久挂起
    def wakeup():
        callback(*args)
    
    import threading
    threading.Timer(0.01, wakeup).start()
    return handle

def register_value_change_callback(
    signal: gpi_sim_hdl, func: Callable[..., Any], edge: int, *args: Any
) -> gpi_cb_hdl:
    """注册一个在信号值改变（上升沿、下降沿或任何改变）时触发的回调。"""
    return gpi_cb_hdl()

def stop_simulator() -> None:
    """请求停止仿真器运行。"""
    print("--- [CoMoPy] 仿真器停止 ---")

def clock_create(hdl: gpi_sim_hdl) -> cpp_clock:
    """创建一个 C++ 侧的时钟加速器。"""
    return cpp_clock(hdl.hdl)

def initialize_logger(
    log_func: Callable[["Logger", int, str, int, str, str], None],
    get_logger: Callable[[str], "Logger"],
) -> None:
    """初始化日志系统，cocotb 会传入其内部的日志处理函数。"""
    pass

def set_sim_event_callback(sim_event_callback: Callable[[], object]) -> None:
    """注册仿真器事件（如开始、停止）的回调。"""
    pass


# 绑定所有方法到 sim 模块
sim.gpi_sim_hdl = gpi_sim_hdl
sim.gpi_cb_hdl = gpi_cb_hdl
sim.gpi_iterator_hdl = gpi_iterator_hdl
sim.cpp_clock = cpp_clock
# 映射17个接口
sim.get_precision = get_precision
sim.get_root_handle = get_root_handle
sim.get_sim_time = get_sim_time
sim.get_simulator_product = get_simulator_product
sim.get_simulator_version = get_simulator_version
sim.is_running = is_running
sim.set_gpi_log_level = set_gpi_log_level
sim.package_iterate = package_iterate
sim.register_nextstep_callback = register_nextstep_callback
sim.register_readonly_callback = register_readonly_callback
sim.register_rwsynch_callback = register_rwsynch_callback
sim.register_timed_callback = register_timed_callback
sim.register_value_change_callback = register_value_change_callback
sim.stop_simulator = stop_simulator
sim.clock_create = clock_create
sim.initialize_logger = initialize_logger
sim.set_sim_event_callback = set_sim_event_callback


# === 4. 模块注入 ===

import sys
import cocotb

# 1. 基础注入
sys.modules["cocotb.simulator"] = sim
cocotb.simulator = sim

# 2. 扫描并强制修复所有已加载的 cocotb 子模块
for name, mod in sys.modules.items():
    if name.startswith("cocotb") and mod is not None:
        try:
            # 如果模块内部有 simulator 属性，强制覆盖
            if hasattr(mod, "simulator"):
                setattr(mod, "simulator", sim)
        except Exception:
            pass

print("--- [CoMoPy] Cocotb internal submodules patched ---")