from comopy.hdl import *


# _______ 组合逻辑__________
# 1. 简单门电路：与门

class Andgate(RawModule):
    @build
    def ports(s):
        s.a = Input()
        s.b = Input()
        s.out = Output()
    @build
    def connect(s):
        s.out @= s.a & s.b 

# 2. 算术组合逻辑：5位加法器
class SimpleAdder(Module):
    @build
    def ports(s):
        s.a = Input(5)
        s.b = Input(5)
        s.q = Output(5)

    @comb
    def update(s):
        s.q /= s.a + s.b  # 使用 /= 在组合逻辑块中赋值

# 3. 复杂算术逻辑：16位加法器 (带进位)

class add16(RawModule):
    @build
    def build_all(s):
        s.a = Input(16)
        s.b = Input(16)
        s.cin = Input()
        s.sum = Output(16)
        s.cout = Output()
        
        s.full_res = Logic(17) # 内部逻辑信号
        s.full_res @= s.a.ext(17) + s.b.ext(17) + s.cin.ext(17)
        
        s.sum  @= s.full_res[:16] # 截取低16位
        s.cout @= s.full_res[16]  # 截取最高进位位

# 4. 层次化组合逻辑：32位加法器
class Module_add(RawModule):
    @build
    def build_all(s):
        s.a = Input(32)
        s.b = Input(32)
        s.sum = Output(32)

        s.lo = add16() # 例化低16位
        s.hi = add16() # 例化高16位

        # 级联连接
        s.lo.a    @= s.a[:16]
        s.lo.b    @= s.b[:16]
        s.lo.cin  @= 0
        s.sum[:16] @= s.lo.sum

        s.hi.a    @= s.a[16:]
        s.hi.b    @= s.b[16:]
        s.hi.cin  @= s.lo.cout  # 进位传递
        s.sum[16:] @= s.hi.sum



class Reduction(RawModule):
    """https://hdlbits.01xz.net/wiki/Reduction"""

    @build
    def build_all(s):
        s.in_ = Input(8)
        s.parity = Output()
        s.parity @= s.in_.P



class Always_casez(RawModule):
    """https://hdlbits.01xz.net/wiki/Always_casez"""

    @build
    def build_all(s):
        s.in_ = Input(8)
        s.pos = Output(3)

    @comb
    def update(s):
        match s.in_:
            case "????_???1":
                s.pos /= 0
            case "????_??10":
                s.pos /= 1
            case "????_?100":
                s.pos /= 2
            case "????_1000":
                s.pos /= 3
            case "???1_0000":
                s.pos /= 4
            case "??10_0000":
                s.pos /= 5
            case "?100_0000":
                s.pos /= 6
            case "1000_0000":
                s.pos /= 7
            case _:
                s.pos /= 0

# _______ 时序逻辑__________
# 1. 基础存储单元：8位D触发器

class my_dff8(Module):
    @build
    def build_all(s):
        s.d = Input(8)
        s.q = Output(8)

    @seq
    def update_ff(s):
        s.q <<= s.d  # 使用 <<= 表示非阻塞赋值/时序更新

# 2. 基础存储单元：通用8位寄存器

class SimpleReg(RawModule):
    @build
    def ports(s):
        s.clk = Input()
        s.d = Input(8)
        s.q = Output(8)
    @seq
    def update(s, posedge="clk"):
        s.q <<= s.d

# 3. 混合逻辑：带时序输出的加法器

class Adder(RawModule):
    @build
    def ports(s):
        s.clk = Input(1)
        s.a = Input(5)
        s.b = Input(5)
        s.q = Output(5)
        s.q_ff = Output(5)

    @comb
    def update(s):
        s.q /= s.a + s.b  # 组合部分
    
    @seq
    def update_ff(s, posedge="clk"):
        s.q_ff <<= s.a + s.b # 时序部分，结果在下一拍有效

# 4. 复杂时序系统：8位移位选择模块

class Module_shift8(Module):
    @build
    def build_all(s):
        s.d = Input(8)
        s.sel = Input(2)
        s.q = Output(8)
        # 串行级联的触发器组
        s.dff0 = my_dff8(s.d)
        s.dff1 = my_dff8(s.dff0.q)
        s.dff2 = my_dff8(s.dff1.q)

    @comb
    def update(s):
        # 组合逻辑选择器：根据 sel 选择不同节拍的输出
        match s.sel:
            case 0: s.q /= s.d
            case 1: s.q /= s.dff0.q
            case 2: s.q /= s.dff1.q
            case 3: s.q /= s.dff2.q

class my_dff(RawModule):  # passthrough only for testing
    @build
    def build_all(s):
        s.clk = Input()
        s.d = Input()
        s.q = Output()
        s.q @= s.d


class Module_shift(RawModule):
    """https://hdlbits.01xz.net/wiki/Module_shift"""

    @build
    def build_all(s):
        s.clk = Input()
        s.d = Input()
        s.q = Output()
        s.a = Logic()
        s.b = Logic()
        s.dff0 = my_dff(s.clk, s.d, s.a)
        s.dff1 = my_dff(s.clk, s.a, s.b)
        s.dff2 = my_dff(s.clk, s.b, s.q)
        