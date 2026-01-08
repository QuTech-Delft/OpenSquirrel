from __future__ import annotations

from copy import deepcopy
from functools import partial
from typing import Any

from typing_extensions import Self

from opensquirrel.circuit import Circuit
from opensquirrel.default_instructions import default_instruction_set
from opensquirrel.ir import IR, AsmDeclaration, Bit, BitLike, Instruction, Qubit, QubitLike
from opensquirrel.register_manager import BitRegister, QubitRegister, RegisterManager

_builder_dynamic_attributes = (*default_instruction_set, "asm")


class CircuitBuilder:
    """
    A class using the builder pattern to make construction of circuits easy from Python.
    Adds corresponding instruction when a method is called. Checks that instructions are known and called with the right
    arguments.
    Mainly here to allow for Qiskit-style circuit construction:

    Args:
        qubit_register_size (int): Size of the qubit register
        bit_register_size (int): Size of the bit register

    Example:
        >>> CircuitBuilder(qubit_register_size=3, bit_register_size=3).\
        H(0).CNOT(0, 1).CNOT(0, 2).\
        to_circuit()
        version 3.0
        <BLANKLINE>
        qubit[3] q
        <BLANKLINE>
        h q[0]
        cnot q[0], q[1]
        cnot q[0], q[2]
        <BLANKLINE>
    """

    def __init__(self, qubit_register_size: int, bit_register_size: int = 0) -> None:
        self.register_manager = RegisterManager(QubitRegister(qubit_register_size), BitRegister(bit_register_size))
        self.ir = IR()

    def __dir__(self) -> list[str]:
        return super().__dir__() + list(_builder_dynamic_attributes)  # type: ignore

    def __getattr__(self, attr: str) -> Any:
        if attr in _builder_dynamic_attributes:
            return partial(self._add_statement, attr)
        # Default behaviour
        return self.__getattribute__(attr)

    def _check_qubit_out_of_bounds_access(self, qubit: QubitLike) -> None:
        """Throw error if qubit index is outside the qubit register range.

        Args:
            qubit: qubit to check.
        """
        index = Qubit(qubit).index
        if index >= self.register_manager.get_qubit_register_size():
            msg = f"qubit index {index} is out of bounds"
            raise IndexError(msg)

    def _check_bit_out_of_bounds_access(self, bit: BitLike) -> None:
        """Throw error if bit index is outside the bit register range.

        Args:
            bit: bit to check.
        """
        index = Bit(bit).index
        if index >= self.register_manager.get_bit_register_size():
            msg = f"bit index {index} is out of bounds"
            raise IndexError(msg)

    def _check_out_of_bounds_access(self, instruction: Instruction) -> None:
        for qubit in instruction.qubit_operands:
            self._check_qubit_out_of_bounds_access(qubit)

        for bit in instruction.bit_operands:
            self._check_bit_out_of_bounds_access(bit)

    def _add_statement(self, attr: str, *args: Any) -> Self:
        if attr == "asm":
            try:
                asm_declaration = AsmDeclaration(*args)
                self.ir.add_asm_declaration(asm_declaration)
            except TypeError:
                msg = f"trying to build '{attr}' with the wrong number or type of arguments: '{args}'"
                raise TypeError(msg) from None
            return self

        if attr not in default_instruction_set:
            msg = f"unknown instruction '{attr}'"
            raise ValueError(msg)
        try:
            instruction = default_instruction_set[attr](*args)
        except TypeError as e:
            msg = f"trying to build {attr!r} with the wrong number or type of arguments: {args!r}: {e}"
            raise TypeError(msg) from e

        self._check_out_of_bounds_access(instruction)

        self.ir.add_statement(instruction)
        return self

    def to_circuit(self) -> Circuit:
        return Circuit(deepcopy(self.register_manager), deepcopy(self.ir))
