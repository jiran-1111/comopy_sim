from __future__ import annotations

from .circuit_object import CircuitObject, IODirection
from .connectable import Connectable
from .signal import Signal


class StructView:
    """Read-only integer view of a PackedStruct with named field access."""

    _MISSING = object()

    def __init__(
        self,
        struct_cls: type[PackedStruct],
        _value: int | str | object = _MISSING,
        **kwargs,
    ) -> None:
        if _value is not self._MISSING and kwargs:
            cls_name = struct_cls.__name__
            raise TypeError(
                f"{cls_name}.view() cannot mix positional value "
                "and field kwargs."
            )

        self._cls = struct_cls
        self._layout = self._compute_layout(struct_cls)

        if _value is not self._MISSING:
            assert isinstance(_value, (int, str))
            self._value = int(_value)
        else:
            self._value = self._pack_fields(kwargs)

    @staticmethod
    def _compute_layout(struct_cls: type[PackedStruct]) -> dict[str, tuple]:
        field_names = []
        for name, obj in vars(struct_cls).items():
            if not isinstance(obj, Signal):
                continue
            if hasattr(PackedStruct, name):
                continue
            field_names.append(name)

        layout = {}
        offset = 0
        for name in reversed(field_names):
            obj = getattr(struct_cls, name)
            nbits = obj.nbits

            if isinstance(obj, PackedStruct):
                assert False, "UNIMPLEMENTED"

            layout[name] = (offset, nbits, None)
            offset += nbits

        return layout

    def _pack_fields(self, field_values: dict) -> int:
        value = 0
        for name, field_val in field_values.items():
            if name not in self._layout:
                cls_name = self._cls.__name__
                raise AttributeError(f"'{cls_name}' has no field '{name}'.")
            offset, width, _ = self._layout[name]
            mask = (1 << width) - 1
            value |= (field_val & mask) << offset
        return value

    def __getattr__(self, name: str) -> int | StructView:
        if name not in self._layout:
            cls_name = self._cls.__name__
            raise AttributeError(f"'{cls_name}' has no field '{name}'.")

        offset, width, nested_cls = self._layout[name]
        mask = (1 << width) - 1
        field_value = (self._value >> offset) & mask

        if nested_cls is not None:
            assert False, "UNIMPLEMENTED"

        return field_value

    def __int__(self) -> int:
        return self._value


class PackedStruct(Signal):
    _field_names: list[str]
    _fields: list[CircuitObject]

    def __init__(self, link: Connectable | None = None) -> None:
        cls = self.__class__
        width = 0
        self._field_names = []
        for name, obj in vars(cls).items():
            if not isinstance(obj, Signal):
                continue
            if hasattr(PackedStruct, name):
                raise ValueError(
                    f"Cannot overwrite attribute '{name}' of PackedStruct."
                )
            if obj.direction is not None:
                raise ValueError(
                    f"Directed signal '{name}' in "
                    f"packed structure '{cls.__name__}'."
                    "\n- Use IOStruct to organize directed I/O ports."
                )
            assert not obj.is_parameterized
            width += obj.nbits
            self._field_names.append(name)
        if width == 0:
            raise ValueError(f"Empty packed structure '{cls.__name__}'.")
        super().__init__(width, link)
        self._fields = []

    def create(
        self, link: Connectable | None = None, *, flipped: bool = False
    ) -> PackedStruct:
        assert not self.is_parameterized
        new = self.__class__(link)
        assert new._nbits == self._nbits
        if self.direction is not None:
            if flipped:
                new._direction = self.direction.flip()
            else:
                new._direction = self.direction
        return new

    @property
    def all_fields(self) -> list[CircuitObject]:
        assert self.assembled
        return self._fields

    @classmethod
    def view(cls, _value=StructView._MISSING, **kwargs) -> StructView:
        return StructView(cls, _value, **kwargs)

    def assemble(self) -> None:
        stop = self._nbits
        for name in self._field_names:
            obj = getattr(self.__class__, name)
            assert isinstance(obj, Signal)
            nbits = obj.nbits
            field = obj.create(self[stop - nbits : stop])
            setattr(self, name, field)
            self._fields.append(field)
            stop -= nbits
        assert stop == 0