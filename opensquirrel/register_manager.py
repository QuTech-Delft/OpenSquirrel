from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterator
from typing import Any, ClassVar

DEFAULT_QUBIT_REGISTER_NAME = "q"
DEFAULT_BIT_REGISTER_NAME = "b"


class Register:
    """Register manages a (virtual) register."""

    default_name: ClassVar[str]

    def __init__(
        self,
        size: int,
        name: str,
        virtual_zero_index: int = 0,
    ) -> None:
        self._size = size
        self._name = name
        self._virtual_zero_index = virtual_zero_index

    @property
    def name(self) -> str:
        return self._name

    @property
    def size(self) -> int:
        return self._size

    @property
    def virtual_zero_index(self) -> int:
        return self._virtual_zero_index

    @virtual_zero_index.setter
    def virtual_zero_index(self, value: int) -> None:
        self._virtual_zero_index = value

    def __getitem__(self, key: int | slice) -> Any:
        if isinstance(key, int):
            if abs(key) >= len(self):
                msg = f"Index {key} is out of range"
                raise IndexError(msg)
            size = len(self) if key < 0 else 0
            return self._virtual_zero_index + key + size
        if isinstance(key, slice):
            start, stop, step = key.indices(len(self))
            return list(range(start + self._virtual_zero_index, stop + self._virtual_zero_index, step))

    def __len__(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[int]:
        index = self._virtual_zero_index
        while index < self._virtual_zero_index + self._size:
            yield index
            index += 1

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Register):
            return False
        return (
            self.size == other.size and self.name == other.name and self.virtual_zero_index == other.virtual_zero_index
        )

    def __repr__(self) -> str:
        return f"{type(self)}: {self.name}, {self.size}"


class QubitRegister(Register):
    """QubitRegister manages a (virtual) qubit register."""

    default_name: ClassVar[str] = DEFAULT_QUBIT_REGISTER_NAME

    def __init__(self, size: int, name: str = default_name) -> None:
        super().__init__(size, name=name)


class BitRegister(Register):
    """BitRegister manages a (virtual) bit register."""

    default_name: ClassVar[str] = DEFAULT_BIT_REGISTER_NAME

    def __init__(self, size: int, name: str = default_name) -> None:
        super().__init__(size, name=name)


QubitRegistry = OrderedDict[str, QubitRegister]
BitRegistry = OrderedDict[str, BitRegister]
Registry = QubitRegistry | BitRegistry


class RegisterManager:
    def __init__(self, qubit_registry: QubitRegistry, bit_registry: BitRegistry) -> None:
        self._qubit_registry = qubit_registry
        self._bit_registry = bit_registry
        self._virtual_qubit_register = (
            QubitRegister(0) if not qubit_registry else (RegisterManager.generate_virtual_register(qubit_registry))
        )
        self._virtual_bit_register = (
            BitRegister(0) if not bit_registry else (RegisterManager.generate_virtual_register(bit_registry))
        )

    @staticmethod
    def generate_virtual_register(registry: Registry) -> Register:
        registers = list(registry.values())
        register_cls = registers[0].__class__
        virtual_index = 0
        for register in registers:
            register.virtual_zero_index = virtual_index
            virtual_index += register.size
        return register_cls(virtual_index, register_cls.default_name)

    def add_qubit_register(self, qubit_register: QubitRegister) -> None:
        if qubit_register.name in self._qubit_registry:
            msg = f"Qubit register with name '{qubit_register.name}' already exists"
            raise KeyError(msg)
        self._qubit_registry[qubit_register.name] = qubit_register
        self._virtual_qubit_register = RegisterManager.generate_virtual_register(self._qubit_registry)

    def add_bit_register(self, bit_register: BitRegister) -> None:
        if bit_register.name in self._bit_registry:
            msg = f"Bit register with name '{bit_register.name}' already exists"
            raise KeyError(msg)
        self._bit_registry[bit_register.name] = bit_register
        self._virtual_bit_register = RegisterManager.generate_virtual_register(self._bit_registry)

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
        return self._qubit_registry[qubit_register_name]

    def get_bit_register(self, bit_register_name: str) -> BitRegister:
        return self._bit_registry[bit_register_name]

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
