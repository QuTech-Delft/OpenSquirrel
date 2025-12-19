from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Iterable, List, Tuple

import cqasm.v3x as cqasm
from opensquirrel.ir import Qubit, Bit

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
    """Abstract base class for managing a (virtual) register."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the register."""

    @staticmethod
    @abstractmethod
    def is_of_type(variable: cqasm.semantic.MultiVariable) -> bool:
        """Check if the variable matches the register type."""

    def __init__(
        self,
        register_size: int,
        name: str,
        variable_name_to_range: dict[str, Range] | None = None,
        index_to_variable_name: dict[int, str] | None = None,
    ) -> None:
        self.register_size: int = register_size
        self._name: str = name
        self.variable_name_to_range: dict[str, Range] = variable_name_to_range or {}
        self.index_to_variable_name: dict[int, str] = index_to_variable_name or {}

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, Register)
            and self.register_size == other.register_size
            and self.variable_name_to_range == other.variable_name_to_range
            and self.index_to_variable_name == other.index_to_variable_name
        )

    def __contains__(self, other: Any) -> bool:
        return isinstance(other, (Qubit, Bit)) and other.index in self.index_to_variable_name

    def get_variable_name(self, index: int) -> str:
        return self.index_to_variable_name[index]

    def get_range(self, variable_name: str) -> Range:
        return self.variable_name_to_range[variable_name]

    def get_index(self, variable_name: str, sub_index: int) -> int:
        return self.variable_name_to_range[variable_name].first + sub_index

    def __repr__(self) -> str:
        entries = ", ".join(f"{name}: {rng}" for name, rng in self.variable_name_to_range.items())
        return f"Register(name={self._name}, size={self.register_size}, ranges={{ {entries} }})"

    def size(self) -> int:
        return self.register_size

    @classmethod
    def from_ast(cls, ast: cqasm.semantic.Program) -> list["Register"]:
        instances = []
        current_qubit_index = 0
        current_bit_index = 0

        for v in ast.variables:
            if is_bit_type(v) or is_qubit_type(v):
                v_name = v.name
                v_size = v.typ.size
                if is_qubit_type(v):
                    variable_name_to_range = {v_name: Range(current_qubit_index, v_size)}
                    index_to_variable_name = {
                        i: v_name for i in range(current_qubit_index, current_qubit_index + v_size)
                    }
                    instance = QubitRegister(v_size, name=v_name,
                                             variable_name_to_range=variable_name_to_range,
                                             index_to_variable_name=index_to_variable_name)
                    current_qubit_index += v_size
                else:
                    variable_name_to_range = {v_name: Range(current_bit_index, v_size)}
                    index_to_variable_name = {
                        i: v_name for i in range(current_bit_index, current_bit_index + v_size)
                    }
                    instance = BitRegister(v_size, name=v_name,
                                            variable_name_to_range=variable_name_to_range,
                                            index_to_variable_name=index_to_variable_name)
                    current_bit_index += v_size

                instances.append(instance)
        return instances


class QubitRegister(Register):
    """Concrete class for managing a qubit register."""

    def __init__(
        self,
        register_size: int,
        name: str = "q",
        variable_name_to_range: dict[str, Range] | None = None,
        index_to_variable_name: dict[int, str] | None = None,
    ) -> None:
        self.register_size = register_size
        if variable_name_to_range is None and index_to_variable_name is None:
            variable_name_to_range = {name: Range(register_size)}
            index_to_variable_name = {i: name for i in range(register_size)}
        super().__init__(register_size, name, variable_name_to_range, index_to_variable_name)

    @property
    def name(self) -> str:
        return self._name

    @staticmethod
    def is_of_type(variable: cqasm.semantic.MultiVariable) -> bool:
        return is_qubit_type(variable)


class BitRegister(Register):
    """Concrete class for managing a bit register."""

    def __init__(
        self,
        register_size: int,
        name: str = "b",
        variable_name_to_range: dict[str, Range] | None = None,
        index_to_variable_name: dict[int, str] | None = None,
    ) -> None:
        self.register_size = register_size
        super().__init__(register_size, name, variable_name_to_range, index_to_variable_name)

    @property
    def name(self) -> str:
        return self._name

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

    def __init__(self, *args: Register | Iterable[Register]) -> None:
        
        """
        Initialize a QuantumCircuit with given registers.

        Parameters
        ----------
        *args : Register
            One or more Register objects (QubitRegister or BitRegister).

        Raises
        ------
        TypeError
            If any argument is not an instance of Register.
        """

        
        registers: List[Register] = []
        for arg in args:
            if isinstance(arg, Register):
                registers.append(arg)
            elif isinstance(arg, Iterable):
                if not all(isinstance(r, Register) for r in arg):
                    raise TypeError("All elements in iterable must be of type Register.")
                registers.extend(arg)
            else:
                raise TypeError("Arguments must be Register or Iterable[Register].")

        self.qubit_registers, self.bit_registers = self.split_registers(registers)

        self.num_qubits = self._get_total_qubit_register_size()
        self.num_bits = self._get_total_bit_register_size()

    def __repr__(self) -> str:
        return f"qubit_register:\n{self.qubit_registers}\nbit_register:\n{self.bit_registers}"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, RegisterManager):
            return False
        return self.qubit_registers == other.qubit_registers and self.bit_registers == other.bit_registers

    def __contains__(self, obj: Any) -> bool:
        
        if isinstance(obj, QubitRegister):
            for qubit_register in self.qubit_registers:
                if obj.name == qubit_register.name:
                    return True
        
        if isinstance(obj, BitRegister):
            for bit_register in self.bit_registers:
                if obj.name == bit_register.name:
                    return True                

        if isinstance(obj, Qubit):
            for qubit_register in self.qubit_registers:
                if obj in qubit_register:
                    return True

        if isinstance(obj, Bit):
            for bit_register in self.bit_registers:
                if obj in bit_register:
                    return True
        
        return False

    
    
    @staticmethod
    def split_registers(registers: Iterable[Register]) -> Tuple[List[QubitRegister], List[BitRegister]]:
        """
        Split a collection of registers into qubit and bit registers.

        Parameters
        ----------
        registers : Iterable[Register]
            An iterable of Register objects.

        Returns
        -------
        Tuple[List[QubitRegister], List[BitRegister]]
            A tuple containing two lists: one for QubitRegister objects and one for BitRegister objects.
        """
        qubits: List[QubitRegister] = []
        bits: List[BitRegister] = []

        for reg in registers:
            if isinstance(reg, QubitRegister):
                qubits.append(reg)
            elif isinstance(reg, BitRegister):
                bits.append(reg)
            else:
                raise TypeError(f"Unsupported register type: {type(reg).__name__}")

        return qubits, bits



    def _get_total_qubit_register_size(self) -> int:
        size = 0
        for qubit_register in self.qubit_registers:
            size += self.get_qubit_register_size(qubit_register)
        
        return size

    def _get_total_bit_register_size(self) -> int:
        size = 0
        for bit_register in self.bit_registers:
            size += self.get_bit_register_size(bit_register)
        
        return size

    def get_qubit_register_size(self, qubit_register: QubitRegister | str | None = None) -> int:
        
        """
        Retrieve the size of a specified qubit register.

        Parameters
        ----------
        qubit_register : Optional qubit register to return size  

        Returns
        -------
        int
            The size of the matching qubit register, or 0 if `qubit_register` is None.

        Raises
        ------
        ValueError
            If the specified register (by name or object) is not found in `self.qubit_registers`.
        """

        if qubit_register is None:
            size = 0
            
            for register in self.qubit_registers:
                register.register_size += size
            
            return size
        for register in self.qubit_registers:
            if isinstance(qubit_register, str) and register.name == qubit_register:
                return register.size()
            elif qubit_register == register:
                return register.size()
        
        raise ValueError(f"Register {qubit_register} not found")


    def get_bit_register_size(self, bit_register: BitRegister | str | None = None) -> int:
        
        """
        Retrieve the size of a specified bit register.

        Parameters
        ----------
        qubit_register : Optional bit register to return size  

        Returns
        -------
        int
            The size of the matching bit register, or 0 if `qubit_register` is None.

        Raises
        ------
        ValueError
            If the specified register (by name or object) is not found in `self.bit_registers`.
        """

        if bit_register is None:
            size = 0
            
            for register in self.bit_registers:
                register.register_size += size
            
            return size
        for register in self.bit_registers:
            if isinstance(bit_register, str) and register.name == bit_register:
                return register.size()
            elif bit_register == register:
                return register.size()
        
        raise ValueError(f"Register {bit_register} not found")

    def get_qubit_register_name(self, qubit_register: QubitRegister | None = None) -> str:
        for register in self.qubit_registers:
            if qubit_register is None:
                return self.qubit_registers[0].name
            if qubit_register == register:
                return qubit_register.name
            
        return ""
        

    def get_bit_register_name(self, bit_register: BitRegister | None = None) -> str:

        for register in self.bit_registers:
            if bit_register is None:
                return self.bit_registers[0].name
            if bit_register == register:
                return bit_register.name
        
        return ""
        

    def get_qubit_range(self, qubit_register: QubitRegister | str, variable_name: str) -> Range:
        for register in self.qubit_registers:
            if isinstance(qubit_register, str) and register.name == qubit_register:
                return register.get_range(variable_name)
            elif qubit_register == register:
                return register.get_range(variable_name)
        
        raise ValueError(f"Register {qubit_register} not found")

    def get_bit_range(self, bit_register: BitRegister | str, variable_name: str) -> Range:
        
        for register in self.bit_registers:
            if isinstance(bit_register, str) and register.name == bit_register:
                return register.get_range(variable_name)
            elif bit_register == register:
                return register.get_range(variable_name)
        
        raise ValueError(f"Register {bit_register} not found")

    def get_qubit_index(self, qubit_register: QubitRegister | str, variable_name: str, sub_index: int) -> int:
        
        for register in self.qubit_registers:
            if isinstance(qubit_register, str) and register.name == qubit_register:
                return register.get_index(variable_name, sub_index)
            elif qubit_register == register:
                return register.get_index(variable_name, sub_index)
        
        raise ValueError(f"Register {qubit_register} not found")

    def get_bit_index(self, bit_register: BitRegister | str, variable_name: str, sub_index: int) -> int:
        
        for register in self.bit_registers:
            if isinstance(bit_register, str) and register.name == bit_register:
                return register.get_index(variable_name, sub_index)
            elif bit_register == register:
                return register.get_index(variable_name, sub_index)
        
        raise ValueError(f"Register {bit_register} not found")

    def get_qubit_variable_name(self, qubit_register: QubitRegister | str, index: int) -> str:
        
        for register in self.qubit_registers:
            if isinstance(qubit_register, str) and register.name == qubit_register:
                return register.get_variable_name(index)
            elif qubit_register == register:
                return register.get_variable_name(index)
        
        raise ValueError(f"Register {qubit_register} not found")

    def get_bit_variable_name(self, bit_register: BitRegister | str, index: int) -> str:

        for register in self.bit_registers:
            if isinstance(bit_register, str) and register.name == bit_register:
                return register.get_variable_name(index)
            elif bit_register == register:
                return register.get_variable_name(index)
        
        raise ValueError(f"Register {bit_register} not found")

