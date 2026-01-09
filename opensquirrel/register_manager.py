from __future__ import annotations

from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import Any, Type

QUBIT_REGISTER_NAME = "q"
BIT_REGISTER_NAME = "b"


class Register(ABC):
    """Register manages a (virtual) register."""

    def __init__(
        self,
        size: int,
        name: str,
        virtual_index_0: int = 0,
    ) -> None:
        self._size = size
        self._name = name
        self._virtual_index_0 = virtual_index_0

    @property
    def name(self) -> str:
        return self._name

    @property
    def size(self) -> int:
        return self._size

    @property
    def virtual_index_0(self) -> int:
        return self._virtual_index_0

    @virtual_index_0.setter
    def virtual_index_0(self, value: int) -> None:
        self._virtual_index_0 = value

    def __getitem__(self, index: int) -> Any:
        if index > self._size:
            msg = f"Index {index} is out of range"
            raise IndexError(msg)
        return self._virtual_index_0 + index

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Register):
            return False
        return self._size == other.size and self._name == other.name and self._virtual_index_0 == other.virtual_index_0

    def __repr__(self) -> str:
        return f"{type(self)}: {self.name}, {self.size}"


class QubitRegister(Register):
    """QubitRegister manages a (virtual) qubit register."""

    _default_name: str = QUBIT_REGISTER_NAME

    def __init__(self, size: int, name: str = _default_name) -> None:
        super().__init__(size, name=name)


class BitRegister(Register):
    """BitRegister manages a (virtual) bit register."""

    _default_name: str = BIT_REGISTER_NAME

    def __init__(self, size: int, name: str = _default_name) -> None:
        super().__init__(size, name=name)


Registry = OrderedDict[str, QubitRegister | BitRegister]


class RegisterManager:
    def __init__(self, qubit_registry: Registry, bit_registry: Registry) -> None:
        self._qubit_registry = qubit_registry
        self._bit_registry = bit_registry
        self._virtual_qubit_register = RegisterManager.generate_virtual_register(
            qubit_registry
        ) or QubitRegister(0)
        self._virtual_bit_register = RegisterManager.generate_virtual_register(
            bit_registry
        ) or BitRegister(0)

    @staticmethod
    def generate_virtual_register(registry: Registry) -> QubitRegister | BitRegister | None:
        registers = list(registry.values())
        if not registers:
            return None
        register_cls = registers[0].__class__
        virtual_index = 0
        for register in registers:
            register.virtual_index_0 = virtual_index
            virtual_index += register.size
        return register_cls(virtual_index)

    def add_qubit_register(self, qubit_register: QubitRegister) -> None:
        self._qubit_registry[qubit_register.name] = qubit_register

    def add_bit_register(self, bit_register: BitRegister) -> None:
        self._bit_registry[bit_register.name] = bit_register

    @property
    def qubit_register_size(self) -> int:
        return self._virtual_qubit_register.size

    @property
    def qubit_register_name(self) -> str:
        return self._virtual_qubit_register.name

    @property
    def bit_register_size(self) -> int:
        return self._virtual_bit_register.size

    @property
    def bit_register_name(self) -> str:
        return self._virtual_bit_register.name

    def get_qubit_register(self, qubit_register_name: str) -> QubitRegister:
        return self._qubit_registry[qubit_register_name]  # type: ignore[return-value]

    def get_bit_register(self, bit_register_name: str) -> BitRegister:
        return self._bit_registry[bit_register_name]  # type: ignore[return-value]

    def __repr__(self) -> str:
        return (
            f"virtual_qubit_register:\n{self._virtual_qubit_register}\n"
            f"virtual_bit_register:\n{self._virtual_bit_register}"
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, RegisterManager):
            return False
        return (
            self._virtual_qubit_register == other._virtual_qubit_register
            and self._virtual_bit_register == other._virtual_bit_register
        )
