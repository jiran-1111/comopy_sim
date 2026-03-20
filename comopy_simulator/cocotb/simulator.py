from __future__ import annotations
import sys
import os
from types import ModuleType
from typing import Callable, Any, TYPE_CHECKING
import logging
# 静态检查时导入
if TYPE_CHECKING:
    from cocotb.handle import GPIDiscovery
    from logging import Logger
else:
    GPIDiscovery = Any
    Logger = Any

# === 类定义 (对应 GPI 接口) ===

class cpp_clock:
    def __init__(self, signal: 'gpi_sim_hdl') -> None:
        self.signal = signal
    def start(self, period_steps: int, high_steps: int, start_high: bool, set_action: int) -> None:
        pass
    def stop(self) -> None:
        pass

class gpi_sim_hdl:
    def __init__(self, name: str, obj: Any = None, sim_engine: Any = None):
        self.name = name
        self.obj = obj          # 存储 CoMoPy 的硬件对象
        self.sim = sim_engine   # 存储 EventSimulator 实例
        self.hdl = self

    def get_const(self) -> bool: return False
    def get_definition_file(self) -> str: return "virtual.v"
    def get_definition_name(self) -> str: return "logic"
    def get_handle_by_index(self, index: int) -> 'gpi_sim_hdl | None': return None
    
    def get_handle_by_name(self, name: str, discovery_method: int = 0) -> 'gpi_sim_hdl' | None:
        return None

    def get_indexable(self) -> bool: return False
    def get_name_string(self) -> str: return self.name
    def get_num_elems(self) -> int: return getattr(self.obj, 'nbits', 0)
    def get_range(self) -> tuple[int, int, int]: return (0, 0, 0)
    
    def get_signal_val_binstr(self) -> str: return "0"
    def get_signal_val_long(self) -> int:
        if hasattr(self.obj, 'data_bits'):
            return self.obj.data_bits.unsigned
        return 0
    def get_signal_val_real(self) -> float: return 0.0
    def get_signal_val_str(self) -> bytes: return b""

    def get_type(self) -> int:
        # 动态检测对象类型
        try:
            from comopy.hdl import RawModule
            if isinstance(self.obj, RawModule): return 2 # MODULE
        except: pass
        return 15 # LOGIC

    def get_type_string(self) -> str: 
        return "MODULE" if self.get_type() == 2 else "LOGIC"

    def iterate(self, mode: int) -> 'gpi_iterator_hdl': return gpi_iterator_hdl()

    def set_signal_val_int(self, action: int, value: int) -> None: 
        # 核心：驱动信号并触发电路评估
        if hasattr(self.obj, '__itruediv__'):
            self.obj /= value
            if self.sim: self.sim.evaluate()

    def set_signal_val_binstr(self, action: int, value: str) -> None: pass
    def set_signal_val_real(self, action: int, value: float) -> None: pass
    def set_signal_val_str(self, action: int, value: bytes) -> None: pass
    def __eq__(self, other: object) -> bool: return isinstance(other, gpi_sim_hdl) and self.name == other.name
    def __hash__(self) -> int: return hash(self.name)
    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

class gpi_cb_hdl: 
    """对应 C++ 中的 GpiCbHdl 类。代表一个已注册的回调（如 Timer, Edge）。"""
    def deregister(self): 
        """取消已注册的回调，使其不再触发。"""
        pass
    def __eq__(self, other: object) -> bool: return self is other
    def __ne__(self, other: object) -> bool: return not self.__eq__(other)
    def __hash__(self) -> int: return id(self)

class gpi_iterator_hdl: 
    """对应 C++ 中的 GpiIteratorHdl 类。用于遍历层级。"""
    def __eq__(self, other: object) -> bool: return self is other
    def __ne__(self, other: object) -> bool: return not self.__eq__(other)
    def __hash__(self) -> int: return id(self)
    def __iter__(self) : return self
    def __next__(self) -> gpi_sim_hdl: 
        raise StopIteration

# === 全局定义的 GPI 接口函数 17个 ===

def get_precision() -> int: return -9
def get_sim_time() -> tuple[int, int]: 
    return 0,0

def get_simulator_product() -> str: return "CoMoPy"
def get_simulator_version() -> str: return "1.0"
def is_running() -> bool: return True
def set_gpi_log_level(level: int) -> None: pass
def package_iterate() -> gpi_iterator_hdl: return gpi_iterator_hdl()
def register_nextstep_callback(func, *args): return gpi_cb_hdl()
def register_readonly_callback(func, *args): return gpi_cb_hdl()
def register_rwsynch_callback(func, *args): return gpi_cb_hdl()

def register_timed_callback(time_steps, callback, *args):
    """
    当 Cocotb 执行 await Timer 时，会调用这个函数。
    我们必须在一段时间后执行 callback(*args)，Cocotb 才会继续往下走。
    """
    # 模拟真实世界的时间延迟（比如 10ms 后叫醒 Cocotb）
    import threading
    t = threading.Timer(0.01, lambda: callback(*args))
    t.start()
    
    return gpi_cb_hdl()

def register_value_change_callback(signal, func, edge, *args): return gpi_cb_hdl()
def stop_simulator(): print("--- [CoMoPy] Simulator Stopped ---")
def clock_create(hdl: gpi_sim_hdl): return cpp_clock(hdl.hdl)

def initialize_logger(
    log_func: Callable[["Logger", int, str, int, str, str], None],
    get_logger: Callable[[str], "Logger"],
) -> None:
   
    from cocotb.logging import _configure
    _configure(None)
  
    
    cocotb_log = logging.getLogger("cocotb")
    cocotb_log.setLevel(logging.DEBUG)

    log_file = "cocotb_simulation.log"
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    
    if cocotb_log.handlers:
        file_handler.setFormatter(cocotb_log.handlers[0].formatter)
    else:
        file_handler.setFormatter(logging.Formatter('%(levelname)-8s %(name)-20s %(message)s'))
    
    cocotb_log.addHandler(file_handler)
    
    print(f"--- [CoMoPy] Logging redirected to: {os.path.abspath(log_file)} ---")

def set_sim_event_callback(sim_event_callback): pass

def get_root_handle(name: str | None) -> gpi_sim_hdl | None: 
    return gpi_sim_hdl(name if name else "top",
                        obj = name,
                        sim_engine=name)

# === 注入核心函数 ===


def patch_cocotb_simulator(comopy_sim_instance):
    """
    通过 sys.modules 注入伪造的 simulator 模块。
    """
    sim = ModuleType("cocotb.simulator")

    # 注入常量
    constants = {
        "DRIVERS": 2, "ENUM": 7, "GENARRAY": 12, "INTEGER": 10, "LOADS": 3,
        "LOGIC": 15, "LOGIC_ARRAY": 16, "MEMORY": 1, "MODULE": 2, "NETARRAY": 10,
        "OBJECTS": 1, "PACKAGE": 13, "REAL": 9, "STRING": 11, "STRUCTURE": 8,
        "PACKED_STRUCTURE": 14, "UNKNOWN": 0, "RISING": 0, "FALLING": 1,
        "VALUE_CHANGE": 2, "RANGE_UP": 1, "RANGE_DOWN": -1, "RANGE_NO_DIR": 0,
    }
    for name, val in constants.items():
        setattr(sim, name, val)

    # 绑定外部定义的函数到该模块
    sim.get_precision = get_precision
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
    sim.get_root_handle = get_root_handle
    

    # 绑定类定义
    sim.gpi_sim_hdl = gpi_sim_hdl
    sim.gpi_cb_hdl = gpi_cb_hdl
    sim.gpi_iterator_hdl = gpi_iterator_hdl
    sim.cpp_clock = cpp_clock

    # 执行系统替换
    sys.modules["cocotb.simulator"] = sim
    
    import cocotb
    cocotb.simulator = sim

    # 如果已经导入 把simulator 模块的引用替换成新的 sim 对象
    for name, mod in list(sys.modules.items()):
        if name.startswith("cocotb") and mod is not None:
            try:
                if hasattr(mod, "simulator"):
                    setattr(mod, "simulator", sim)
            except: pass

    print("--- [CoMoPy] Cocotb Simulator successfully patched ---")
    return sim