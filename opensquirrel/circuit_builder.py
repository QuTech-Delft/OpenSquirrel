from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from functools import partial
from typing import Any

from typing_extensions import Self

from opensquirrel.circuit import Circuit
from opensquirrel.default_instructions import default_instruction_set, default_two_qubit_gate_set
from opensquirrel.ir import IR, AsmDeclaration, Bit, BitLike, Instruction, Qubit, QubitLike
from opensquirrel.register_manager import (
    DEFAULT_BIT_REGISTER_NAME,
    DEFAULT_QUBIT_REGISTER_NAME,
    BitRegister,
    QubitRegister,
    Register,
    RegisterManager,
)

_builder_dynamic_attributes = (*default_instruction_set, "asm")


class CircuitBuilder:
    """
    A class using the builder pattern to make construction of circuits easy from Python.
    Adds corresponding instruction when a method is called. Checks that instructions are known and
    called with the right arguments.
    Mainly here to allow for Qiskit-style circuit construction:

    Args:
        qubit_register_size (int): Size of the qubit register
        bit_register_size (int): Size of the bit register

    Example:
        ```python
        >>> CircuitBuilder(qubit_register_size=3, bit_register_size=3).H(0).CNOT(0, 1).CNOT(0, 2).to_circuit()
        ```
        ```
        version 3.0

        qubit[3] q

        h q[0]
        cnot q[0], q[1]
        cnot q[0], q[2]

        ```
    """

    def __init__(
        self,
        qubit_register_size: int = 0,
        bit_register_size: int = 0,
    ) -> None:
        initial_qubit_registry = (
            OrderedDict({DEFAULT_QUBIT_REGISTER_NAME: QubitRegister(qubit_register_size)})
            if (qubit_register_size > 0)
            else OrderedDict()
        )
        initial_bit_registry = (
            OrderedDict({DEFAULT_BIT_REGISTER_NAME: BitRegister(bit_register_size)})
            if (bit_register_size > 0)
            else OrderedDict()
        )
        self.register_manager = RegisterManager(
            initial_qubit_registry,
            initial_bit_registry,
        )
        self.ir = IR()

    def __dir__(self) -> list[str]:
        return super().__dir__() + list(_builder_dynamic_attributes)  # type: ignore

    def __getattr__(self, attr: str) -> Any:
        if attr in _builder_dynamic_attributes:
            return partial(self._add_statement, attr)
        # Default behaviour
        return self.__getattribute__(attr)

    def add_register(self, register: QubitRegister | BitRegister) -> None:
        """Add a (qu)bit register to the circuit builder.

        Args:
            register (QubitRegister | BitRegister): (Qu)bit register to add.

        """
        self.register_manager.add_register(register)

    def _check_qubit_out_of_bounds_access(self, qubit: QubitLike) -> None:
        """Throw error if qubit index is outside the qubit register range.

        Args:
            qubit: qubit to check.
        """
        index = Qubit(qubit).index
        qubit_register_size = self.register_manager.qubit_register_size
        if index >= qubit_register_size:
            msg = f"qubit index {index!r} is out of bounds: must be smaller than {qubit_register_size!r}"
            raise IndexError(msg)

    def _check_bit_out_of_bounds_access(self, bit: BitLike) -> None:
        """Throw error if bit index is outside the bit register range.

        Args:
            bit: bit to check.
        """
        index = Bit(bit).index
        bit_register_size = self.register_manager.bit_register_size
        if index >= bit_register_size:
            msg = f"bit index {index!r} is out of bounds: must be smaller than {bit_register_size!r}"
            raise IndexError(msg)

    def _check_out_of_bounds_access(self, instruction: Instruction) -> None:
        for qubit in instruction.qubit_operands:
            self._check_qubit_out_of_bounds_access(qubit)

        for bit in instruction.bit_operands:
            self._check_bit_out_of_bounds_access(bit)

    @staticmethod
    def _expand_sgmq_arg(arg: Any) -> list[Any]:
        if isinstance(arg, Register):
            return list(arg)
        if isinstance(arg, list):
            return arg
        return [arg]

    def _add_statement(self, attr: str, *args: Any) -> Self:
        if attr == "asm":
            try:
                asm_declaration = AsmDeclaration(*args)
                self.ir.add_asm_declaration(asm_declaration)
            except TypeError:
                msg = f"trying to build {attr!r} with the wrong number or type of arguments: {args!r}"
                raise TypeError(msg) from None
            return self

        if attr not in default_instruction_set:
            msg = f"unknown instruction {attr!r}"
            raise ValueError(msg)

        sgmq_args = self._expand_sgmq_args(attr, args)

        for expanded_args in sgmq_args:
            try:
                instruction = default_instruction_set[attr](*expanded_args)
            except TypeError as e:
                msg = f"trying to build {attr!r} with the wrong number or type of arguments: {expanded_args!r}: {e}"
                raise TypeError(msg) from e

            self._check_out_of_bounds_access(instruction)
            self.ir.add_statement(instruction)

        return self

    def _expand_sgmq_args(self, attr: str, args: tuple[Any, ...]) -> list[tuple[Any, ...]]:
        if not isinstance(args[0], (Register, list)):
            return [args]

        is_two_operand_instruction = attr in default_two_qubit_gate_set or attr == "measure"

        if len(args) > 1 and is_two_operand_instruction:
            second_expandable = isinstance(args[1], (Register, list))

            if second_expandable:
                expanded_first = self._expand_sgmq_arg(args[0])
                expanded_second = self._expand_sgmq_arg(args[1])

                if len(expanded_first) != len(expanded_second):
                    msg = (
                        f"SGMQ requires matching operand lengths: got {len(expanded_first)} and {len(expanded_second)}"
                    )
                    raise ValueError(msg)

                remaining_args = args[2:]
                return [
                    (first, second, *remaining_args)
                    for first, second in zip(expanded_first, expanded_second, strict=True)
                ]

            msg = (
                "SGMQ notation for multi-operand instructions requires operands to be "
                "lists or registers (and of equal length)"
            )
            raise ValueError(msg)

        expanded_first = self._expand_sgmq_arg(args[0])
        remaining_args = args[1:]
        return [(first, *remaining_args) for first in expanded_first]

    def clear(self) -> None:
        """Clears all statements from the IR."""
        self.ir.clear()

    def to_circuit(self) -> Circuit:
        """Build the circuit.

        Returns:
            Circuit: The built circuit.

        """
        return Circuit(deepcopy(self.register_manager), deepcopy(self.ir))
