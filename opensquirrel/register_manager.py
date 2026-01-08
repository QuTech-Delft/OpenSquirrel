from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, OrderedDict

import cqasm.v3x as cqasm


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

    def __init__(
        self,
        size: int,
        name: str,
        register_variable_to_range: dict[str, Range] | None = None,
        virtual_index_to_register_variable: dict[int, str] | None = None,
    ) -> None:
        self._size: int = size
        self._name: str = name
        self.register_variable_to_range: dict[str, Range] = register_variable_to_range or {}
        self.virtual_index_to_register_variable: dict[int, str] = virtual_index_to_register_variable or {}

    @classmethod
    def from_ast(cls, ast: cqasm.semantic.Program) -> Register:
        register_variables = [register_variable for register_variable in ast.variables
                              if cls.is_of_type(register_variable)]

        register_variable_to_range: dict[str, Range] = {}
        virtual_index_to_register_variable: dict[int, str] = {}
        virtual_index: int = 0
        for register_variable in register_variables:
            register_variable_name = register_variable.name
            register_variable_size = register_variable.typ.size
            register_variable_to_range[register_variable_name] = Range(virtual_index, register_variable_size)
            for _ in range(register_variable_size):
                virtual_index_to_register_variable[virtual_index] = register_variable_name
                virtual_index += 1
        size = sum(variable.typ.size for variable in register_variables)
        name = cls.default_name()
        return cls(
            size=size,
            name=name,
            register_variable_to_range=register_variable_to_range,
            virtual_index_to_register_variable=virtual_index_to_register_variable
        )

    @property
    def size(self) -> int:
        return self._size

    @property
    def name(self) -> str:
        return self._name

    @staticmethod
    @abstractmethod
    def is_of_type(variable: cqasm.semantic.MultiVariable) -> bool: ...

    @staticmethod
    @abstractmethod
    def default_name() -> str: ...

    def get_register_variable(self, index: int) -> str:
        """Get the register variable at `index`."""
        return self.virtual_index_to_register_variable[index]

    def get_range(self, register_variable: str) -> Range:
        """Get the Range for a `register_variable`."""
        return self.register_variable_to_range[register_variable]

    def get_index(self, register_variable: str, sub_index: int) -> int:
        """Get the Index for a given `subIndex` of a `register_variable`."""
        return self.register_variable_to_range[register_variable].first + sub_index

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Register):
            return False
        return (
            self._size == other.size
            and self.register_variable_to_range == other.register_variable_to_range
            and self.virtual_index_to_register_variable == other.virtual_index_to_register_variable
        )

    def __getitem__(self, index: int) -> int:
        register_variable = self.get_register_variable(index)
        return self.get_index(register_variable, index)

    def __repr__(self) -> str:
        entries: str = ""
        first: bool = True
        for register_variable, register_range in self.register_variable_to_range.items():
            entries += "{}{}: {}".format("" if first else ", ", register_variable, register_range)
            first = False
        return f"{{ {entries} }}"


class QubitRegister(Register):
    """QubitRegister manages a (virtual) qubit register."""

    def __init__(
        self,
        size: int,
        name: str = 'q',
        register_variable_to_range: dict[str, Range] | None = None,
        virtual_index_to_register_variable: dict[int, str] | None = None,
    ) -> None:
        super().__init__(size, name, register_variable_to_range, virtual_index_to_register_variable)

    @staticmethod
    def default_name() -> str:
        return 'q'

    @staticmethod
    def is_of_type(variable: cqasm.semantic.MultiVariable) -> bool:
        return is_qubit_type(variable)


class BitRegister(Register):
    """BitRegister manages a (virtual) bit register."""

    def __init__(
        self,
        size: int,
        name: str = 'b',
        register_variable_to_range: dict[str, Range] | None = None,
        virtual_index_to_register_variable: dict[int, str] | None = None,
    ) -> None:
        super().__init__(size, name, register_variable_to_range, virtual_index_to_register_variable)

    @staticmethod
    def default_name() -> str:
        return 'b'

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

    def __init__(self, virtual_qubit_register: QubitRegister, virtual_bit_register: BitRegister) -> None:
        self._qubit_registers: OrderedDict[str, Register] = OrderedDict()
        self._bit_registers: OrderedDict[str, Register] = OrderedDict()
        self._virtual_qubit_register: QubitRegister = virtual_qubit_register
        self._virtual_bit_register: BitRegister = virtual_bit_register

    @classmethod
    def from_ast(cls, ast: cqasm.semantic.Program) -> RegisterManager:
        virtual_qubit_register = QubitRegister.from_ast(ast)
        virtual_bit_register = BitRegister.from_ast(ast)
        register_manager = cls(virtual_qubit_register, virtual_bit_register)
        register_manager._qubit_registers[virtual_qubit_register.name] = virtual_qubit_register
        register_manager._bit_registers[virtual_bit_register.name] = virtual_bit_register
        return register_manager

    def add_qubit_register(self, qubit_register: QubitRegister) -> None:
        self._qubit_registers[qubit_register.name] = qubit_register
        self.generate_virtual_qubit_register()

    def add_bit_register(self, bit_register: BitRegister) -> None:
        self._bit_registers[bit_register.name] = bit_register
        self.generate_virtual_bit_register()

    def generate_virtual_qubit_register(self) -> None:
        register_to_range = {}
        virtual_index_to_register = {}
        virtual_index = 0
        size = 0
        for register_name, register in self._qubit_registers.items():
            register_size = register.size
            size += register_size
            register_to_range[register_name] = Range(virtual_index, register_size)
            for _ in range(register_size):
                virtual_index_to_register[virtual_index] = register_name
                virtual_index += 1
        self._virtual_qubit_register = QubitRegister(
            size=size,
            name='q',
            register_variable_to_range=register_to_range,
            virtual_index_to_register_variable=virtual_index_to_register,
        )

    def generate_virtual_bit_register(self) -> None:
        register_to_range = {}
        virtual_index_to_register = {}
        virtual_index = 0
        size = 0
        for register_name, register in self._qubit_registers.items():
            register_size = register.size
            size += register_size
            register_to_range[register_name] = Range(virtual_index, register_size)
            for _ in range(register_size):
                virtual_index_to_register[virtual_index] = register_name
                virtual_index += 1
        self._virtual_bit_register = BitRegister(
            size=size,
            name='b',
            register_variable_to_range=register_to_range,
            virtual_index_to_register_variable=virtual_index_to_register,
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, RegisterManager):
            return False
        return (self._virtual_qubit_register == other._virtual_qubit_register
                and self._virtual_bit_register == other._virtual_bit_register)

    def __repr__(self) -> str:
        return f"qubit_register:\n{self._virtual_qubit_register}\nbit_register:\n{self._virtual_bit_register}"

    def get_qubit_register_size(self) -> int:
        return self._virtual_qubit_register.size

    def get_bit_register_size(self) -> int:
        return self._virtual_bit_register.size

    def get_qubit_register_name(self) -> str:
        return self._virtual_qubit_register.name

    def get_bit_register_name(self) -> str:
        return self._virtual_bit_register.name

    def get_qubit_range(self, variable_name: str) -> Range:
        return self._virtual_qubit_register.get_range(variable_name)

    def get_bit_range(self, variable_name: str) -> Range:
        return self._virtual_bit_register.get_range(variable_name)

    def get_qubit_index(self, variable_name: str, sub_index: int) -> int:
        return self._virtual_qubit_register.get_index(variable_name, sub_index)

    def get_bit_index(self, variable_name: str, sub_index: int) -> int:
        return self._virtual_bit_register.get_index(variable_name, sub_index)

    def get_qubit_variable_name(self, index: int) -> str:
        return self._virtual_qubit_register.get_register_variable(index)

    def get_bit_variable_name(self, index: int) -> str:
        return self._virtual_bit_register.get_register_variable(index)
