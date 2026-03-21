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
        self.obj = obj 
        self.sim = sim_engine 
        self.hdl = self
        # 显式绑定，确保 cocotb 底层调用的是这个驱动函数
        self._set_value = self.set_signal_val_int

    def get_const(self) -> bool: return False
    def get_definition_file(self) -> str: return "virtual.v"
    def get_definition_name(self) -> str: return "logic"
    def get_handle_by_index(self, index: int) -> 'gpi_sim_hdl | None': return None
    
    def get_handle_by_name(self, name: str, discovery_method: int = 0) -> 'gpi_sim_hdl' | None:
        # 在 RawModule assemble 之后，端口 a, q 会直接作为属性
        target = getattr(self.obj, name, None)
        if target is None and hasattr(self.obj, '_ports'):
            for p in self.obj._ports:
                if getattr(p, 'name', '') == name:
                    target = p
                    break
        if target is not None:
            return gpi_sim_hdl(name=name, obj=target, sim_engine=self.sim)
        return None

    def get_indexable(self) -> bool: return False
    def get_name_string(self) -> str: return self.name
    def get_num_elems(self) -> int: 
        return getattr(self.obj, 'nbits', 1)

    def get_range(self) -> tuple[int, int, int]: 
        # 修正：cocotb 期望返回 (left, right, direction)
        # 对于 3-bit 信号 [2:0]，应该是 (2, 0, -1) 代表 downto
        nbits = self.get_num_elems()
        return (nbits - 1, 0, -1)
    
    def get_signal_val_binstr(self) -> str:
        val = self.get_signal_val_long()
        nbits = self.get_num_elems()
        return bin(val)[2:].zfill(nbits)

    def get_signal_val_long(self) -> int:
        try:
            # CoMoPy/PyMTL3 信号对象读取真实值的标准方法
            if hasattr(self.obj, 'uint'):
                return int(self.obj.uint())
            return int(self.obj)
        except:
            return 0

    def get_signal_val_real(self) -> float: return 0.0
    def get_signal_val_str(self) -> bytes: return b""

    def get_type(self) -> int:
        # 判定是否为模块（Hierarchy）
        if hasattr(self.obj, '_ports') or (hasattr(self.obj, 'is_module') and self.obj.is_module):
            return 2 # MODULE
        # 判定是否为向量或标量
        return 16 if self.get_num_elems() > 1 else 15

    def get_type_string(self) -> str: 
        return "MODULE" if self.get_type() == 2 else "LOGIC"

    def iterate(self, mode: int) -> 'gpi_iterator_hdl': return gpi_iterator_hdl()

    def set_signal_val_int(self, action: int, value: int) -> None: 
        
        """
        这个函数是 Cocotb 最终会通过 C 接口调用的驱动入口
        """
        try:
            # 1. 硬件赋值 (PyMTL3 /= 语法)
            self.obj /= value 
            
            # 2. 立即触发逻辑评估 (核心！否则 q 还是旧值)
            # 这里的 self.sim 是你在 get_root_handle 里传入的 comopy_sim_instance
            if self.sim and hasattr(self.sim, 'evaluate'):
                self.sim.evaluate()
            
            # 强行打印一条信息到终端，证明驱动执行了
            print(f"DEBUG: [CoMoPy Drive] {self.name} = {value}")
        except Exception as e:
            print(f"DEBUG: [Drive Failed] {e}")
    def set_signal_val_binstr(self, action: int, value: str) -> None:
        self.set_signal_val_int(0, int(value, 2))

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
current_time_ps = 0

def get_precision() -> int: return -12
def get_sim_time() -> tuple[int, int]: 
    global current_time_ps
    t = int(current_time_ps)
    # 按照 Cocotb C++ 层的预期返回 (high, low)
    # 使用 0xFFFFFFFF 掩码确保它们是标准的 32 位无符号整数
    low = t & 0xFFFFFFFF
    high = (t >> 32) & 0xFFFFFFFF
    return (high, low)  # 换个顺序试试，如果不行就换回 (low, high)

def get_simulator_product() -> str: return "CoMoPy"
def get_simulator_version() -> str: return "1.0"
def is_running() -> bool: return True
def set_gpi_log_level(level: int) -> None: pass
def package_iterate() -> gpi_iterator_hdl: return gpi_iterator_hdl()
def register_nextstep_callback(func, *args): return gpi_cb_hdl()
def register_readonly_callback(func, *args): return gpi_cb_hdl()
def register_rwsynch_callback(func, *args): return gpi_cb_hdl()

def register_timed_callback(time_steps, callback, *args):
    global current_time_ps
    # time_steps 通常是由 cocotb 根据精度换算过来的整数
    # 如果 Timer(2, "ns") 且 precision=-12, 则 time_steps=2000
    
    current_time_ps += time_steps
    
    # 获取根句柄对应的仿真引擎并评估
    # 我们需要确保在 cocotb 检查结果前，硬件逻辑已经跑过一次 evaluate
    # 注意：这里的 sim_engine 需要从你的全局存储中获取
    
    callback(*args)
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
    import cocotb
    import cocotb.simulator
    import cocotb.simtime
    import sys
    from types import ModuleType

    # 1. 创建伪造模块
    sim = ModuleType("cocotb.simulator")
    
    # 2. 注入所有必需的常量 (补全 cocotb 预期的所有 key)
    constants = {
        "DRIVERS": 2, "ENUM": 7, "GENARRAY": 12, "INTEGER": 10, "LOADS": 3,
        "LOGIC": 15, "LOGIC_ARRAY": 16, "MEMORY": 1, "MODULE": 2, "NETARRAY": 10,
        "OBJECTS": 1, "PACKAGE": 13, "REAL": 9, "STRING": 11, "STRUCTURE": 8,
        "PACKED_STRUCTURE": 14, "UNKNOWN": 0, "RISING": 0, "FALLING": 1,
        "VALUE_CHANGE": 2, "RANGE_UP": 1, "RANGE_DOWN": -1, "RANGE_NO_DIR": 0,
    }
    for name, val in constants.items():
        setattr(sim, name, val)

    # 3. 绑定我们实现的 GPI 函数
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
    
    # 这里的 root handle 是关键
    def get_real_root_handle(name: str | None) -> gpi_sim_hdl | None:
        return gpi_sim_hdl(name=name if name else "top", 
                           obj=comopy_sim_instance.module, 
                           sim_engine=comopy_sim_instance)
    sim.get_root_handle = get_real_root_handle
    
    # 绑定类定义
    sim.gpi_sim_hdl = gpi_sim_hdl
    sim.gpi_cb_hdl = gpi_cb_hdl
    sim.gpi_iterator_hdl = gpi_iterator_hdl
    sim.cpp_clock = cpp_clock
# 4. 【核心黑科技：全路径覆盖】
    sys.modules["cocotb.simulator"] = sim
    cocotb.simulator = sim

    # 暴力遍历所有已加载的 cocotb 子模块
    # 因为很多模块（如 _gpi_triggers, regression 等）会在顶部执行 'from cocotb import simulator'
    # 我们必须把它们手里的那个引用也换掉
    import cocotb
    for mod_name, module in sys.modules.items():
        if mod_name.startswith("cocotb.") and module is not None:
            if hasattr(module, "simulator"):
                setattr(module, "simulator", sim)
                # print(f"DEBUG: Patched {mod_name}.simulator") # 调试用

    # 针对报错最多的几个模块进行显式强刷
    import cocotb._gpi_triggers
    import cocotb.regression
    import cocotb.simtime
    import cocotb.handle
    cocotb._gpi_triggers.simulator = sim
    cocotb.regression.simulator = sim
    cocotb.simtime.simulator = sim
    cocotb.handle.simulator = sim

    # 5. --- 属性拦截保持不变 ---
    import cocotb.handle
    
    def forced_value_setter(self, value):
        val_int = int(value)
        # 直接写硬件
        self._handle.obj /= val_int
        # 立即评估逻辑
        if self._handle.sim and hasattr(self._handle.sim, 'evaluate'):
            self._handle.sim.evaluate()
        # 调试输出
        sys.__stdout__.write(f"\n[CRITICAL HOOK] {self._path} SET TO {val_int}\n")
        sys.__stdout__.flush()

    # 强行覆盖 LogicObject 和 LogicArrayObject 的 value 属性
    # 使用 setattr 动态替换 property，这是最稳妥的办法
    new_prop = property(fget=lambda self: self._handle.get_signal_val_long(), 
                        fset=forced_value_setter)
    
    cocotb.handle.LogicObject.value = new_prop
    if hasattr(cocotb.handle, "LogicArrayObject"):
        cocotb.handle.LogicArrayObject.value = new_prop

    print("--- [CoMoPy] SYSTEM OVERRIDE SUCCESSFUL ---")
    return sim