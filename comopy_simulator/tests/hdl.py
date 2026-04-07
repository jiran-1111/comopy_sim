from comopy.hdl import *

class my_dff8(Module):
    @build
    def build_all(s):
        s.d = Input(8)
        s.q = Output(8)

    @seq
    def update_ff(s):
        s.q <<= s.d

class Module_shift8(Module):
    """https://hdlbits.01xz.net/wiki/Module_shift8"""

    @build
    def build_all(s):
        s.d = Input(8)
        s.sel = Input(2)
        s.q = Output(8)
        s.dff0 = my_dff8(s.d)
        s.dff1 = my_dff8(s.dff0.q)
        s.dff2 = my_dff8(s.dff1.q)

    @comb
    def update(s):
        match s.sel:
            case 0:
                s.q /= s.d
            case 1:
                s.q /= s.dff0.q
            case 2:
                s.q /= s.dff1.q
            case 3:
                s.q /= s.dff2.q

# 基础组合逻辑：与门
class Andgate(RawModule):
    @build
    def ports(s):
        s.a = Input()
        s.b = Input()
        s.out = Output()
    @build
    def connect(s):
        s.out @= s.a & s.b

# Adder 1

class add16(RawModule):
    @build
    def build_all(s):
        s.a = Input(16)
        s.b = Input(16)
        s.cin = Input()
        s.sum = Output(16)
        s.cout = Output()
        
        # 1. 显式定义一个 17 位的临时逻辑信号（实实在在的 ID）
        s.full_res = Logic(17)
        
        # 2. 把计算结果给它
        s.full_res @= s.a.ext(17) + s.b.ext(17) + s.cin.ext(17)
        
        # 3. 像切蛋糕一样切开赋值（避开 cat）
        s.sum  @= s.full_res[:16] # 低 16 位是和
        s.cout @= s.full_res[16]  # 最高位（第 17 位）是进位
        
class Module_add(RawModule):
    """https://hdlbits.01xz.net/wiki/Module_add"""

    @build
    def build_all(s):
        # 1. 定义顶级端口
        s.a = Input(32)
        s.b = Input(32)
        s.sum = Output(32)

        # 2. 显式实例化两个加法器（不带参数）
        s.lo = add16()
        s.hi = add16()

        # 3. 手动连接低位加法器 (lo)
        s.lo.a   @= s.a[:16]
        s.lo.b   @= s.b[:16]
        s.lo.cin @= 0
        s.sum[:16] @= s.lo.sum

        # 4. 手动连接高位加法器 (hi)
        s.hi.a   @= s.a[16:]
        s.hi.b   @= s.b[16:]
        s.hi.cin @= s.lo.cout  # 这里的级联非常关键
        s.sum[16:] @= s.hi.sum

# 时序逻辑：简单寄存器
class SimpleReg(RawModule):
    @build
    def ports(s):
        s.clk = Input()
        s.d = Input(8)
        s.q = Output(8)
    @seq
    def update(s, posedge="clk"):
        s.q <<= s.d

class SimpleAdder(Module):
  
    @build
    def ports(s):

        s.a = Input(5)
        s.b = Input(5)
        s.q = Output(5)

    @comb
    def update(s):
        s.q /= s.a + s.b


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
        s.q /= s.a + s.b
    
    @seq
    def update_ff(s,posedge="clk"):
        # 在 Module 中，@seq 默认监听内置的 s.clk
        s.q_ff <<= s.a + s.b

