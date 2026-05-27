# CORSIC: Co-modeling RISC-V Single-issue In-order Core
#
# Copyright (C) 2026 Microprocessor R&D Center (MPRC), Peking University
# All rights reserved.
#
# Author: Chun Yang



from comopy.hdl import *

from spyre_base import PackedStruct  

# RISC-V instruction
class inst_t(Logic):
    _TYPE_WIDTH = 32


# Register ID
class reg_id_t(Logic):
    _TYPE_WIDTH = 5


# R-type instruction format
class inst_rtype_t(PackedStruct):
    funct7 = Logic(7)
    rs2 = reg_id_t()
    rs1 = reg_id_t()
    funct3 = Logic(3)
    rd = reg_id_t()
    opcode = Logic(7)
