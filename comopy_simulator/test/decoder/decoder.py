from comopy.hdl import *

class Decoder(Module):
    @build
    def ports(s):
        # 输入：32位指令
        s.inst = Input(32)
        
        # 输出：拆解后的控制信号（类似 SimpleDut 的风格）
        s.rd = Output(5)
        s.rs1 = Output(5)
        s.rs2 = Output(5)
        s.alu_op = Output(3)  # 简化为 4bit 编码
        s.is_r_type = Output(1)
        s.is_imm = Output(1)  # 是否是立即数指令

    @comb
    def logic(s):
        # 错误写法：opcode7 = s.inst[0:7]
        # 正确写法：定义一个中间信号（如果需要），或者直接判断
        
        # 1. 如果只是为了判断，可以直接写判断式
        s.is_r_type /= (s.inst[0:7] == 0x33)
        s.is_imm /= (s.inst[0:7] == 0x13)

        # 2. 赋值给端口
        s.rd /= s.inst[7:12]
        s.rs1 /= s.inst[15:20]
        s.rs2 /= s.inst[20:25]
        s.alu_op /= s.inst[12:15]