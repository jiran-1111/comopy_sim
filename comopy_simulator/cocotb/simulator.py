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

_comopy_engine = None 
_current_time_ps = 0
_is_processing = False

import heapq
_event_loop = []

# === 类定义 (对应 GPI 接口) ===

# 没有设置 _impl为gpi 使用python时钟
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
        self._last_value = self.get_signal_val_long()
        self._last_value = self.get_signal_val_long()

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

    """
    def set_signal_val_int(self, action: int, value: int) -> None: 
    
        print(f"\n[HIT] GPI set_signal_val_int called for {self.name} with {value}\n")

        # 使用dut.a._handle.set_signal_val_int(0,2) 可以写入 现在双保险
        # 底层模拟simulator
        # 输出端口禁止写
        print(f"DEBUG: Driving {self.name} with {value}, type is {self.get_definition_name()}")
        if self.get_definition_name() == "output port":
            # 底层也抛出异常
            raise RuntimeError(f"GPI_ERROR: Cannot write to output signal {self.name}")
        
        try:
            # 写硬件
            self.obj /= value 
            
            # 逻辑评估 
            if _comopy_engine:
                # 每次输入改变，立即评估受影响的组合逻辑块
                _comopy_engine.evaluate()
                
            sys.__stdout__.write(f"DEBUG: [CoMoPy Drive] {self.name} = {value}\n")
        except Exception as e:
            sys.__stdout__.write(f"DEBUG: [Drive Failed] {e}\n")
    """
    def set_signal_val_int(self, action, value):
        old_val = self.get_signal_val_long()
        self.obj /= value # 修改硬件值
        
        if _comopy_engine:
            _comopy_engine.evaluate() # 逻辑推导
            
        # 如果是时钟线变了，立即检查边沿触发器
        if self.name == "clk" and old_val != value:
            _check_value_change_callbacks()

    def set_signal_val_binstr(self, action: int, value: str) -> None:
        """支持二进制字符串"""
        # x z简单过滤换成0
        safe_value = value.replace('x', '0').replace('z', '0').replace('u', '0')
        self.set_signal_val_int(0, int(safe_value, 2))
    
    def set_signal_val_real(self, action: int, value: float) -> None:
        """支持浮点数写入，自动四舍五入"""
        val_int = int(round(value))
        #sys.__stdout__.write(f"DEBUG: [Real to Int] Converting {value} to {val_int}\n")
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
            # 优先读取 _data 属性
            raw_data = getattr(self.obj, '_data', None)
            if raw_data is not None:
                return int(raw_data)
            # 如果是信号对象，尝试强转
            return int(self.obj)
        except Exception as e:
            # 不要只打印，给个默认值 0 保证 cocotb 不崩溃
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
回调函数
"""
class gpi_cb_hdl: 
    """对应 C++ 中的 GpiCbHdl 类。代表一个已注册的回调（如 Timer, Edge）。"""
    def __init__(self, event_tuple=None):
        self.event_tuple = event_tuple
        self.active = True
    def deregister(self): 
        """取消已注册的回调，使其不再触发。"""
        self.active = False
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
需要gpi_sim_hdl的iterate方法喂给他数据 待实现
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
_current_time_ps = 0
# ————————————————时间管理类————————————
"""仿真最小单位"""
def get_precision() -> int: return -12

"""返回当前的仿真时间 64位"""
def get_sim_time() -> tuple[int, int]: 
    global _current_time_ps
    t = int(_current_time_ps)
    return (t >> 32 & 0xFFFFFFFF, t & 0xFFFFFFFF)


"""
遍历所有的注册的信号回调
读取信号的当前值 对比存储的旧值
"""

def cleanup_test():
    global _event_loop
    _event_loop.clear()

import comopy.hdl as HDL
_event_count = 0 

# await Timer(10,"ns") 调用register_timed_callback(10000,callback) 目标时间，回调函数


import itertools
import heapq

# 全局变量
_event_loop = []
_cnt = itertools.count() # 修复 NameError: name '_cnt' is not defined
_is_processing = False
_current_time_ps = 0
def register_timed_callback(time_steps, callback, *args):
    global _current_time_ps
    target_time = _current_time_ps + time_steps
    event_packet = [target_time, next(_cnt), callback, args, True]
    heapq.heappush(_event_loop, event_packet)

    # 关键：手动触发一次处理逻辑
    _pump_events() 
    return gpi_cb_hdl(event_packet)

def _pump_events():
    global _current_time_ps, _is_processing
    # 如果已经在处理中，直接返回，让外层的 while 循环继续处理新加入的任务
    if _is_processing: 
        return
    
    _is_processing = True
    try:
        # 使用 while 循环，确保新注册的事件（如连续的 Timer）能被连续处理
        while _event_loop:
            # 检查堆顶事件
            t, cnt, cb, a, active = heapq.heappop(_event_loop)
            
            # 推进仿真时间
            _current_time_ps = t
            
            # 硬件逻辑演进（非常重要！）
            if _comopy_engine:
                # 如果有硬件引擎，执行评估
                _comopy_engine.evaluate()
                # 检查是否因为时间推进触发了边沿（比如时钟翻转）
                _check_value_change_callbacks()

            if active:
                # 执行回调，这会回到 cocotb 协程
                # 如果协程里又有 await Timer，它会往 _event_loop 里推新东西
                cb(*a) 
                
    finally:
        _is_processing = False
# ——————————————回调注册——————————————————————
"""请求在delta step(逻辑重新评估一次后执行回调)"""
def register_nextstep_callback(func, *args): return gpi_cb_hdl()
"""请求在当前仿真时刻的只读阶段执行 实现await readonly"""
def register_readonly_callback(func, *args): return gpi_cb_hdl()
"""在读写同步阶段执行 允许在此阶段读写"""
def register_rwsynch_callback(func, *args): return gpi_cb_hdl()

"""重要 实现await risingedge fallingedge"""

# 所有等待信号变化的协程列表
_value_change_callbacks = []
# 检测边沿是否达到回调条件 如果should_trigger则触发回调

def _check_value_change_callbacks():
    global _value_change_callbacks
    if not _value_change_callbacks: return

    remaining = []
    # 建立一个快照，防止在循环中被修改
    current_callbacks = list(_value_change_callbacks)
    _value_change_callbacks = [] 

    for item in current_callbacks:
        signal, edge_type, cb, args, cb_hdl = item
        if not cb_hdl.active: continue

        new_val = signal.get_signal_val_long()
        old_val = signal._last_value
        
        # 只有真正变化了才处理
        if new_val != old_val:
            is_rising = (old_val == 0 and new_val == 1)
            is_falling = (old_val == 1 and new_val == 0)

            should_trigger = False
            if edge_type == 0: should_trigger = is_rising
            elif edge_type == 1: should_trigger = is_falling
            elif edge_type == 2: should_trigger = True # BOTH

            if should_trigger:
                # 记录日志，看看到底是谁触发的
                #sys.__stdout__.write(f"DEBUG: Triggered {edge_type} on {signal.name}: {old_val}->{new_val}\n")
                cb(*args)
                signal._last_value = new_val # 触发了才更新旧值
                continue # 不再放回 remaining

        remaining.extend([item])
        signal._last_value = new_val # 没触发也得更新旧值，防止下次对比出错

    _value_change_callbacks.extend(remaining)

"""
首先 登记回调
"""
def register_value_change_callback(signal, func, edge, *args):
    """
    edge: 0 为 RISING, 1 为 FALLING, 2 为 BOTH
    """
    global _value_change_callbacks
    # 注册回调
    cb_hdl = gpi_cb_hdl()
    # 加入回调函数队列
    _value_change_callbacks.append((signal, edge, func, args, cb_hdl))
    
    # 打印调试信息
    # sys.__stdout__.write(f"DEBUG: Registered Edge Callback on {signal.name} (Type: {edge})\n")
    
    return cb_hdl

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
"""
def get_root_handle(name: str | None) -> gpi_sim_hdl | None: 
    return gpi_sim_hdl(name if name else "top",
                        obj = name,
                        sim_engine=name)
"""
"""遍历sv里面的package comopy暂无"""
def package_iterate() -> gpi_iterator_hdl: return gpi_iterator_hdl()



# ——————————————系统集成与日志——————————————————

"""所有测试完成时调用 打印结束标志"""
def stop_simulator(): 
    global _event_loop, _current_time_ps
    #print("--- [ComoPy] Cleaning up after test... ---")
    _event_loop.clear()
    #print("--- [CoMoPy] Simulator Stopped ---")
    

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
    
    #print(f"--- [CoMoPy] Logging redirected to: {os.path.abspath(log_file)} ---")

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
    
    def set_signal_val_int(handle, action, value):
        # 这里的 handle 实际上就是 gpi_sim_hdl 的实例
        handle.set_signal_val_int(action, value)

    def get_signal_val_long(handle):
        return handle.get_signal_val_long()
    
    def get_signal_val_binstr(handle):
        return handle.get_signal_val_binstr()

    # 2. 必须显式注入到你伪造的 sim 模块对象中
    sim.set_signal_val_int = set_signal_val_int
    sim.get_signal_val_long = get_signal_val_long
    sim.get_signal_val_binstr = get_signal_val_binstr


    import cocotb.handle
    # _schedule_write 是 cocotb.handle 模块里负责排队写操作的函数，改成直写
    def immediate_write(handle, func, action, *args):
    # handle: LogicArrayObject 实例
    # func: set_signal_val_int
    # action: 写入动作类型 (Deposit/Force等)
    # *args: 具体的数值 (value)
        func(action, *args)

    cocotb.handle._schedule_write = immediate_write

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
    
    #print("--- [CoMoPy] SYSTEM OVERRIDE SUCCESSFUL ---")
    return sim