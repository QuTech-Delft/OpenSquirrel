from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import cqasm.v3x as cqasm
from typing_extensions import Self


def is_qubit_type(variable: cqasm.semantic.MultiVariable) -> bool:
    return isinstance(variable.typ, (cqasm.types.Qubit, cqasm.types.QubitArray))


def is_bit_type(variable: cqasm.semantic.MultiVariable) -> bool:
    return isinstance(variable.typ, (cqasm.types.Bit, cqasm.types.BitArray))


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

    @staticmethod
    @abstractmethod
    def is_of_type(variable: cqasm.semantic.MultiVariable) -> bool: ...

    def __init__(
        self,
        register_size: int,
        variable_name_to_range: dict[str, Range] | None = None,
        index_to_variable_name: dict[int, str] | None = None,
    ) -> None:
        self.register_size: int = register_size
        self.variable_name_to_range: dict[str, Range] = variable_name_to_range or {}
        self.index_to_variable_name: dict[int, str] = index_to_variable_name or {}

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Register):
            return False
        return (
            self.register_size == other.register_size
            and self.variable_name_to_range == other.variable_name_to_range
            and self.index_to_variable_name == other.index_to_variable_name
        )

    def get_variable_name(self, index: int) -> str:
        """Get the variable name at `index`."""
        return self.index_to_variable_name[index]

    def get_range(self, variable_name: str) -> Range:
        """Get the Range for a `variable_name`."""
        return self.variable_name_to_range[variable_name]

    def get_index(self, variable_name: str, sub_index: int) -> int:
        """Get the Index for a given `subIndex` of a `variable_name`."""
        return self.variable_name_to_range[variable_name].first + sub_index

    def __repr__(self) -> str:
        entries: str = ""
        first: bool = True
        for variable_name, register_range in self.variable_name_to_range.items():
            entries += "{}{}: {}".format("" if first else ", ", variable_name, register_range)
            first = False
        return f"{{ {entries} }}"

    def size(self) -> int:
        return self.register_size

    @classmethod
    def from_ast(cls, ast: cqasm.semantic.Program) -> Self:
        variables = [v for v in ast.variables if cls.is_of_type(v)]
        register_size = sum(v.typ.size for v in variables)
        variable_name_to_range: dict[str, Range] = {}
        index_to_variable_name: dict[int, str] = {}

        current_index: int = 0
        for v in variables:
            v_name = v.name
            v_size = v.typ.size
            variable_name_to_range[v_name] = Range(current_index, v_size)
            for _ in range(v_size):
                index_to_variable_name[current_index] = v_name
                current_index += 1
        return cls(register_size, variable_name_to_range, index_to_variable_name)


class QubitRegister(Register):
    """QubitRegister manages a (virtual) qubit register."""

    _default_qubit_register_name: str = "q"

    @property
    def name(self) -> str:
        return self._default_qubit_register_name

    @staticmethod
    def is_of_type(variable: cqasm.semantic.MultiVariable) -> bool:
        return is_qubit_type(variable)


class BitRegister(Register):
    """BitRegister manages a (virtual) bit register."""

    _default_bit_register_name: str = "b"

    @property
    def name(self) -> str:
        return self._default_bit_register_name

    @staticmethod
    def is_of_type(variable: cqasm.semantic.MultiVariable) -> bool:
        return is_bit_type(variable)


class RegisterManager:
    """RegisterManager keeps track of a (virtual) qubit register, i.e., an array of consecutive qubits,
    and the mappings between the (logical) qubit variable names, as used in an input cQASM program,
    and the (virtual) qubit register.

    For example, given an input program that defines 'qubit[3] q':
    - variable 'q' is mapped to qubits 0 to 2 in the qubit register, and
    - positions 0 to 2 in the qubit register are mapped to variable 'q'.

    The mapping of qubit variable names to positions in the qubit register is an implementation detail,
    i.e., it is not guaranteed that qubit register indices are assigned to qubit variable names in the order
    these variables are defined in the input program.
    """

    def __init__(self, qubit_register: QubitRegister, bit_register: BitRegister | None = None) -> None:
        self.qubit_register: QubitRegister = qubit_register
        self.bit_register: BitRegister = bit_register or BitRegister(0)

    def __repr__(self) -> str:
        return f"qubit_register:\n{self.qubit_register}\nbit_register:\n{self.bit_register}"

    @classmethod
    def from_ast(cls, ast: cqasm.semantic.Program) -> Self:
        qubit_register = QubitRegister.from_ast(ast)
        bit_register = BitRegister.from_ast(ast)
        return cls(qubit_register, bit_register)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, RegisterManager):
            return False
        return self.qubit_register == other.qubit_register and self.bit_register == other.bit_register

    def get_qubit_register_size(self) -> int:
        return self.qubit_register.size()

    def get_bit_register_size(self) -> int:
        return self.bit_register.size()

    def get_qubit_register_name(self) -> str:
        return self.qubit_register.name

    def get_bit_register_name(self) -> str:
        return self.bit_register.name

    def get_qubit_range(self, variable_name: str) -> Range:
        return self.qubit_register.get_range(variable_name)

    def get_bit_range(self, variable_name: str) -> Range:
        return self.bit_register.get_range(variable_name)

    def get_qubit_index(self, variable_name: str, sub_index: int) -> int:
        return self.qubit_register.get_index(variable_name, sub_index)

    def get_bit_index(self, variable_name: str, sub_index: int) -> int:
        return self.bit_register.get_index(variable_name, sub_index)

    def get_qubit_variable_name(self, index: int) -> str:
        return self.qubit_register.get_variable_name(index)

    def get_bit_variable_name(self, index: int) -> str:
        return self.bit_register.get_variable_name(index)
