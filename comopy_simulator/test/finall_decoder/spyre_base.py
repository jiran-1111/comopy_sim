from __future__ import annotations
from comopy.hdl import Logic, Signal

# ==========================
# EnumBase 枚举基类
# ==========================
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
                raise ValueError(f"Member {name} must be AUTO or int")
            if isinstance(value, int):
                enum_value = value
            members[name] = enum_value
            enum_value += 1

        if not members:
            raise ValueError("Enum must have at least one member")

        cls._sorted_members = sorted(members, key=lambda k: members[k])
        cls.__check_enum_values(members)
        nbits = (len(members) - 1).bit_length()
        cls._TYPE_WIDTH = nbits

        for name, val in members.items():
            setattr(cls, name, val)

    @classmethod
    def __check_enum_values(cls, members):
        if members[cls._sorted_members[0]] != 0:
            raise ValueError("Enum must start at 0")
        for i in range(len(cls._sorted_members)-1):
            a = cls._sorted_members[i]
            b = cls._sorted_members[i+1]
            if members[a] == members[b]:
                raise ValueError("Duplicate enum value")
            if members[b] != members[a]+1:
                raise ValueError("Enum values must be consecutive")

    @classmethod
    def enum_names(cls):
        return cls._sorted_members

    @property
    def is_typedef_logic(self):
        return False
    @property
    def is_enum(self):
        return True

# ==========================
# PackedStruct 打包结构体（完美修复）
# ==========================
class StructView:
    _MISSING = object()
    def __init__(self, struct_cls, _value=_MISSING, **kwargs):
        if _value is not self._MISSING and kwargs:
            raise TypeError("Cannot mix value and fields")
        self._cls = struct_cls
        self._layout = self._compute_layout(struct_cls)
        self._value = int(_value) if _value is not self._MISSING else self._pack_fields(kwargs)

    @staticmethod
    def _compute_layout(cls):
        fields = []
        for name, obj in vars(cls).items():
            if isinstance(obj, Signal) and not name.startswith("_"):
                fields.append(name)

        layout = {}
        offset = 0
        for name in reversed(fields):
            obj = getattr(cls, name)
            layout[name] = (offset, obj.nbits)
            offset += obj.nbits
        return layout

    def _pack_fields(self, fields):
        val = 0
        for name, v in fields.items():
            off, w = self._layout[name]
            val |= (v & ((1 << w)-1)) << off
        return val

    def __getattr__(self, name):
        off, w = self._layout[name]
        return (self._value >> off) & ((1 << w)-1)

    def __int__(self):
        return self._value

class PackedStruct(Signal):
    _field_names: list[str]

    def __init__(self, link=None):
        cls = self.__class__
        self._field_names = []
        total_width = 0

        for name, obj in vars(cls).items():
            if isinstance(obj, Signal) and not name.startswith("_"):
                self._field_names.append(name)
                total_width += obj.nbits

        super().__init__(total_width, link)

    def create(self, link=None, *, flipped=False):
        new = self.__class__(link)
        if hasattr(self, "_direction") and self._direction is not None:
            new._direction = self._direction.flip() if flipped else self._direction
        return new

    @classmethod
    def view(cls, *args, **kwargs):
        return StructView(cls, *args, **kwargs)

    def assemble(self):
        cls = self.__class__
        current_bit = 0

        for name in reversed(self._field_names):
            field_template = getattr(cls, name)
            w = field_template.nbits
            slice_part = self[current_bit : current_bit + w]
            field = field_template.create(slice_part)
            setattr(self, name, field)
            current_bit += w