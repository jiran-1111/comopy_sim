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

_active_comopy_sim = None
_comopy_engine = None 
_current_time_ps = 0
# === 类定义 (对应 GPI 接口) ===

# 这个clock是否是需要实现的
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
        self._set_value = self.set_signal_val_int

    def get_handle_by_name(self, name: str, discovery_method: int = 0) -> 'gpi_sim_hdl' | None:
        """找到信号对象 返回gpi_sim_hdl对象"""
        target = getattr(self.obj, name, None)
        if target is None and hasattr(self.obj, '_ports'):
            for p in self.obj._ports:
                if getattr(p, 'name', '') == name:
                    target = p
                    break
        if target is not None:
            return gpi_sim_hdl(name=name, obj=target, sim_engine=self.sim)
        else :
            sys.__stdout__.write(f"failes: can not find signal {name} \n")
        return None
    
    def get_type(self) -> int:
        """判定为模块还是信号"""
        if hasattr(self.obj, '_ports') or (hasattr(self.obj, 'is_module') and self.obj.is_module):
            return 2 # MODULE
        # 如果位宽是1 则返回单比特信号 其他为向量信号
        # "LOGIC": 15, "LOGIC_ARRAY": 16
        return 16 if self.get_num_elems() > 1 else 15

    def set_signal_val_int(self, action: int, value: int) -> None: 
        """支持整数写入"""
        # 使用dut.a._handle.set_signal_val_int(0,2) 可以写入 现在双保险
        # 底层模拟simulator
        if self.get_definition_name() == "output port":
            # 底层也抛出异常
            raise RuntimeError(f"GPI_ERROR: Cannot write to output signal {self.name}")
        
        try:
            # 写硬件
            self.obj /= value 
            
            # --- 真正的连接点 A：组合逻辑评估 ---
            if _comopy_engine:
                # 每次输入改变，立即评估受影响的组合逻辑块
                _comopy_engine.evaluate()
                
            sys.__stdout__.write(f"DEBUG: [CoMoPy Drive] {self.name} = {value}\n")
        except Exception as e:
            sys.__stdout__.write(f"DEBUG: [Drive Failed] {e}\n")
    
    def set_signal_val_binstr(self, action: int, value: str) -> None:
        """支持二进制字符串"""
        # x z简单过滤换成0
        safe_value = value.replace('x', '0').replace('z', '0').replace('u', '0')
        self.set_signal_val_int(0, int(safe_value, 2))
    
    def set_signal_val_real(self, action: int, value: float) -> None:
        """支持浮点数写入，自动四舍五入"""
        val_int = int(round(value))
        sys.__stdout__.write(f"DEBUG: [Real to Int] Converting {value} to {val_int}\n")
        self.set_signal_val_int(action, val_int)

    def set_signal_val_str(self, action: int, value: bytes) -> None:
        """支持字节串写入，将其视为大端序整数"""
        try:
            # 尝试将字节转为大整数（大端序）
            val_int = int.from_bytes(value, byteorder='big')
            self.set_signal_val_int(action, val_int)
        except Exception as e:
            sys.__stdout__.write(f"ERROR: [Str Drive Failed] Cannot map {value} to hardware: {e}\n")

    def get_indexable(self) -> bool: 
        """是否支持下标访问 dut.mysignal[0] 待实现"""
        return False
    
    def get_name_string(self) -> str: 
        """"返回信号在硬件层级中的原始名称"""
        return self.name
    
    def get_num_elems(self) -> int: 
        """返回该信号位宽"""
        return getattr(self.obj, 'nbits', 1)

    def get_range(self) -> tuple[int, int, int]: 
        """定义信号的索引范围和方向"""
        # 返回值含义（左边界，右边界，方向） -1 downto
        nbits = self.get_num_elems()
        return (nbits - 1, 0, -1)
    
    def get_const(self) -> bool: 
        """信号是否是常量 为常量则禁止写"""
        return False
    
    def get_definition_file(self) -> str:
        """返回hdl文件名"""
        return "hdl_design.py"

    def get_definition_name(self) -> str:
        """根据属性判断硬件结构 日志使用"""
        # 逻辑：根据 CoMoPy 对象的属性来判定它在硬件里的“角色”
        if self.get_type() == 2: 
            return "module"
        if hasattr(self.obj, 'is_input_port') and self.obj.is_input_port:
            return "input port"
        if hasattr(self.obj, 'is_output_port') and self.obj.is_output_port:
            return "output port"
        return "wire"
    
    def get_handle_by_index(self, index: int) -> 'gpi_sim_hdl | None': 
        """通过索引获取子信号 用于访问数组"""
        return None
 
    def get_signal_val_binstr(self) -> str:
        """将当前的信号值读取为二进制字符串"""
        val = self.get_signal_val_long()
        nbits = self.get_num_elems()
        return bin(val)[2:].zfill(nbits)

    def get_signal_val_long(self) -> int:
        """核心读操作"""
        try:
            # 获取原始数据对象
            raw_data = getattr(self.obj, '_data', None)
            if raw_data is not None:
                return int(raw_data)
            return int(self.obj)
        except Exception as e:
            # sys.__stdout__.write(f"READ ERROR: {e}\n")
            return 0

    def get_signal_val_real(self) -> float: 
        """将当前的信号值读取为浮点数"""
        return 0.0
    
    def get_signal_val_str(self) -> bytes: 
        """将当前的信号值读取为字节串"""
        return b""

    def get_type_string(self) -> str: 
        """返回信号的类型"""
        return "MODULE" if self.get_type() == 2 else "LOGIC"

    def iterate(self, mode: int) -> 'gpi_iterator_hdl': 
        """层次迭代器 未实现 dump依赖该迭代器"""
        return gpi_iterator_hdl()

    def __eq__(self, other: object) -> bool:
        """如果底层硬件对象是同一个，则句柄相同"""
        if not isinstance(other,gpi_sim_hdl):
            return False
        return self.obj is other.obj

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)
    
    def __hash__(self) -> int: 
        """使用底层对象的内存地址作为hash"""
        return id(self.obj)

"""
注册回调函数
"""
class gpi_cb_hdl: 
    """对应 C++ 中的 GpiCbHdl 类。代表一个已注册的回调（如 Timer, Edge）。"""
    def deregister(self): 
        """取消已注册的回调，使其不再触发。"""
        pass
    def __eq__(self, other: object) -> bool:
        """判断两个回调句柄是否相同"""
        return self is other
    def __ne__(self, other: object) -> bool: 
        """判断不等于"""
        return not self.__eq__(other)
    def __hash__(self) -> int: 
        """生成哈希值"""
        return id(self)

"""
需要gpi_sim_hdl的iterate方法喂给他数据
"""
class gpi_iterator_hdl: 
    """对应 C++ 中的 GpiIteratorHdl 类。用于遍历层级。"""
    def __eq__(self, other: object) -> bool: 
        """相等"""
        return self is other
    def __ne__(self, other: object) -> bool: 
        """不等"""
        return not self.__eq__(other)
    def __hash__(self) -> int: 
        """哈希"""
        return id(self)
    def __iter__(self) : 
        """返回迭代器对象本身"""
        return self
    def __next__(self) -> gpi_sim_hdl: 
        """获取下一个信号句柄"""
        raise StopIteration

# === 全局定义的 GPI 接口函数 17个 ===
# 全局时间
current_time_ps = 0
# ————————————————时间管理类————————————
"""仿真最小单位"""
def get_precision() -> int: return -12

"""返回当前的仿真时间 64位"""
def get_sim_time() -> tuple[int, int]: 
    global _current_time_ps
    t = int(_current_time_ps)
    return (t >> 32 & 0xFFFFFFFF, t & 0xFFFFFFFF)

"""重要的时间推进函数"""
# 执行await timer
def register_timed_callback(time_steps, callback, *args):
    global _current_time_ps, _comopy_engine
    
    import comopy.hdl as HDL # 导入用于判断
    
    if _comopy_engine:
        # 检查是否有对应的 Module 实例且具有 clk 属性
        dut_obj = getattr(_comopy_engine, "_module", None)
        
        # 判断：只有当它是真正的 HDL.Module (带有时钟) 时才调用 tick
        if isinstance(dut_obj, HDL.Module) and hasattr(dut_obj, 'clk'):
            num_ticks = time_steps // 1000 
            for _ in range(max(1, num_ticks)):
                _comopy_engine.tick()
        else:
            # 如果是 RawModule (无时钟)，我们只同步逻辑评估，不触发时钟边沿
            # 这样就不会触发 CoMoPy 内部的 RuntimeError 了
            _comopy_engine.evaluate()
            sys.__stdout__.write("DEBUG: [CoMoPy] RawModule detected, skipping tick(), running evaluate() only\n")

    _current_time_ps += time_steps
    callback(*args) # 暂时写成同步 立即执行回调
    return gpi_cb_hdl()

# ——————————————回调注册——————————————————————
"""请求在delta step(逻辑重新评估一次后执行回调)"""
def register_nextstep_callback(func, *args): return gpi_cb_hdl()
"""请求在当前仿真时刻的只读阶段执行 实现await readonly"""
def register_readonly_callback(func, *args): return gpi_cb_hdl()
"""在读写同步阶段执行 允许在此阶段读写"""
def register_rwsynch_callback(func, *args): return gpi_cb_hdl()

"""重要 实现await risingedge fallingedge"""
def register_value_change_callback(signal, func, edge, *args): 
    return gpi_cb_hdl()

"""设置仿真时间的全局回调"""
def set_sim_event_callback(sim_event_callback): pass

# ————————————仿真器元数据——————————————
"""返回仿真器名称"""
def get_simulator_product() -> str: return "CoMoPy"
"""返回版本号"""
def get_simulator_version() -> str: return "1.0"
"""检查仿真器是否在运行"""
def is_running() -> bool: return True

"""获取设计的顶层句柄"""
def get_root_handle(name: str | None) -> gpi_sim_hdl | None: 
    return gpi_sim_hdl(name if name else "top",
                        obj = name,
                        sim_engine=name)
"""遍历sv里面的package comopy暂无"""
def package_iterate() -> gpi_iterator_hdl: return gpi_iterator_hdl()



# ——————————————系统集成与日志——————————————————

"""所有测试完成时调用 打印结束标志"""
def stop_simulator(): 
    print("--- [CoMoPy] Simulator Stopped ---")

"""创建底层时钟对象"""
def clock_create(hdl: gpi_sim_hdl): 
    return cpp_clock(hdl.hdl)

"""接管日志系统"""
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

"""设置底层gpi日志详细程度"""
def set_gpi_log_level(level: int) -> None: pass




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
    global _comopy_engine
    _comopy_engine = comopy_sim_instance  # 这里的实例就是你的 ScheduledSimulator
    
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
    # 全路径覆盖
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
    
    # python的handle层截断后续流程 高层次拦截
   
    
    def forced_value_setter(self, value):
        # 修正：通过 self._handle 调用你定义的 GPI 接口函数
        if self._handle.get_definition_name() == "output port":
            error_msg = f"COCOTB_ERROR: Attempting to drive output port '{self._path}'! This is illegal in hardware."
            # 抛出异常会直接中断当前的 cocotb.test
            raise AttributeError(error_msg) 

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