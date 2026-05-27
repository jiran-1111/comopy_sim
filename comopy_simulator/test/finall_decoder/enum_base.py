# 完全兼容旧版 ComoPy，不依赖任何新版模块
from comopy.hdl import Logic


class _EnumAuto:
    __slots__ = ()
    def __repr__(self) -> str:
        return "AUTO"

AUTO = _EnumAuto()


class EnumBase(Logic):
    _sorted_members: list[str]
    _TYPE_WIDTH: int

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        members = {}
        enum_value = 0
        for name, value in cls.__dict__.items():
            if name.startswith("_"):
                continue
            if value is not AUTO and not isinstance(value, int):
                raise ValueError(f"枚举 {cls.__name__}.{name} 必须是 AUTO 或整数")
            if isinstance(value, int):
                enum_value = value
            members[name] = enum_value
            enum_value += 1

        if not members:
            raise ValueError(f"{cls.__name__} 必须至少有一个枚举成员")

        cls._sorted_members = sorted(members, key=lambda k: members[k])
        cls.__check_enum_values(members)

        num_members = len(members)
        nbits = (num_members - 1).bit_length()
        cls._TYPE_WIDTH = nbits

        # 旧版 ComoPy 兼容：直接用 int，不用 Bits
        for name, val in members.items():
            setattr(cls, name, val)

    @classmethod
    def __check_enum_values(cls, members: dict):
        first = cls._sorted_members[0]
        if members[first] != 0:
            raise ValueError(f"{cls.__name__} 枚举必须从 0 开始")

        for i in range(len(cls._sorted_members)-1):
            a = cls._sorted_members[i]
            b = cls._sorted_members[i+1]
            va = members[a]
            vb = members[b]
            if va == vb:
                raise ValueError(f"{cls.__name__} 重复值 {va}")
            if vb != va + 1:
                raise ValueError(f"{cls.__name__} 值不连续")

    @classmethod
    def enum_names(cls):
        return cls._sorted_members

    @property
    def is_typedef_logic(self) -> bool:
        return False

    @property
    def is_enum(self) -> bool:
        return True