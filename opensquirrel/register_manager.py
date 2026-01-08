from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, OrderedDict


@dataclass
class Range:
    first: int = 0
    size: int = 0

    def __repr__(self) -> str:
        return "[{}{}]".format(self.first, "" if self.size == 1 else f"..{self.first + self.size - 1}")


class Register(ABC):
    """Register manages a (virtual) register."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    def __init__(
        self,
        size: int,
        variable_name_to_range: dict[str, Range] | None = None,
        index_to_variable_name: dict[int, str] | None = None,
    ) -> None:
        self._size: int = size
        self.variable_name_to_range: dict[str, Range] = variable_name_to_range or {}
        self.index_to_variable_name: dict[int, str] = index_to_variable_name or {}

    @property
    def size(self) -> int:
        return self._size

    def get_variable_name(self, index: int) -> str:
        """Get the variable name at `index`."""
        return self.index_to_variable_name[index]

    def get_range(self, variable_name: str) -> Range:
        """Get the Range for a `variable_name`."""
        return self.variable_name_to_range[variable_name]

    def get_index(self, variable_name: str, sub_index: int) -> int:
        """Get the Index for a given `subIndex` of a `variable_name`."""
        return self.variable_name_to_range[variable_name].first + sub_index

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Register):
            return False
        return (
            self._size == other.size
            and self.variable_name_to_range == other.variable_name_to_range
            and self.index_to_variable_name == other.index_to_variable_name
        )

    def __repr__(self) -> str:
        entries: str = ""
        first: bool = True
        for variable_name, register_range in self.variable_name_to_range.items():
            entries += "{}{}: {}".format("" if first else ", ", variable_name, register_range)
            first = False
        return f"{{ {entries} }}"


class QubitRegister(Register):
    """QubitRegister manages a (virtual) qubit register."""

    _default_qubit_register_name: str = "q"

    @property
    def name(self) -> str:
        return self._default_qubit_register_name


class BitRegister(Register):
    """BitRegister manages a (virtual) bit register."""

    _default_bit_register_name: str = "b"

    @property
    def name(self) -> str:
        return self._default_bit_register_name


class RegisterManager:

    def __init__(self, virtual_qubit_register: QubitRegister, virtual_bit_register: BitRegister | None = None) -> None:
        self.virtual_qubit_register: QubitRegister = virtual_qubit_register
        self.virtual_bit_register: BitRegister = virtual_bit_register or BitRegister(0)
        self._qubit_registers: OrderedDict[str, QubitRegister] = OrderedDict()
        self._bit_registers: OrderedDict[str, BitRegister] = OrderedDict()

    @property
    def qubit_register_size(self) -> int:
        return self.virtual_qubit_register.size

    @property
    def bit_register_size(self) -> int:
        return self.virtual_bit_register.size

    @property
    def qubit_register_name(self) -> str:
        return self.virtual_qubit_register.name

    @property
    def bit_register_name(self) -> str:
        return self.virtual_bit_register.name

    def get_qubit_range(self, variable_name: str) -> Range:
        return self.virtual_qubit_register.get_range(variable_name)

    def get_bit_range(self, variable_name: str) -> Range:
        return self.virtual_bit_register.get_range(variable_name)

    def get_qubit_index(self, variable_name: str, sub_index: int) -> int:
        return self.virtual_qubit_register.get_index(variable_name, sub_index)

    def get_bit_index(self, variable_name: str, sub_index: int) -> int:
        return self.virtual_bit_register.get_index(variable_name, sub_index)

    def get_qubit_variable_name(self, index: int) -> str:
        return self.virtual_qubit_register.get_variable_name(index)

    def get_bit_variable_name(self, index: int) -> str:
        return self.virtual_bit_register.get_variable_name(index)

    def __repr__(self) -> str:
        return (f"virtual_qubit_register:\n{self.virtual_qubit_register}\n"
                f"virtual_bit_register:\n{self.virtual_bit_register}")

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, RegisterManager):
            return False
        return (self.virtual_qubit_register == other.virtual_qubit_register
                and self.virtual_bit_register == other.virtual_bit_register)
