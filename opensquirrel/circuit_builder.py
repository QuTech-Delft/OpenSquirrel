from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from functools import partial
from typing import Any

from typing_extensions import Self

from opensquirrel.circuit import Circuit
from opensquirrel.default_instructions import default_instruction_set
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
    def _is_sgmq_expandable(arg: Any) -> bool:
        """Check if an argument should be expanded for SGMQ notation.

        An argument should be expanded if it is:
        - A list (but not a tuple, which is used for axis arguments)
        - A Register (QubitRegister or BitRegister) that is not being used as an index

        Args:
            arg: The argument to check.

        Returns:
            True if the argument should be expanded, False otherwise.

        """
        return isinstance(arg, (Register, list))

    @staticmethod
    def _expand_sgmq_arg(arg: Any) -> list[Any]:
        """Expand an SGMQ argument into a list of individual values.

        Args:
            arg: The argument to expand (Register or list).

        Returns:
            A list of individual values.

        """
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
        if not args:
            return [args]

        expandable_indices = [i for i, arg in enumerate(args) if self._is_sgmq_expandable(arg)]

        if not expandable_indices:
            return [args]

        if attr == "measure":
            return self._expand_measure_args(args, expandable_indices)

        if self._is_tuple_style_sgmq(args):
            return self._expand_tuple_style_args(args)

        if 0 not in expandable_indices:
            return [args]

        expanded_qubits = self._expand_sgmq_arg(args[0])
        remaining_args = args[1:]

        return [(qubit, *remaining_args) for qubit in expanded_qubits]

    @staticmethod
    def _is_tuple_style_sgmq(args: tuple[Any, ...]) -> bool:
        if len(args) < 2:
            return False

        if not all(isinstance(arg, list) for arg in args):
            return False

        first_len = len(args[0])
        if first_len == 0:
            return False

        return all(len(arg) == first_len for arg in args)

    @staticmethod
    def _expand_tuple_style_args(args: tuple[Any, ...]) -> list[tuple[Any, ...]]:
        return [tuple(arg) for arg in args]

    def _expand_measure_args(self, args: tuple[Any, ...], expandable_indices: list[int]) -> list[tuple[Any, ...]]:
        qubit_arg = args[0]
        bit_arg = args[1] if len(args) > 1 else None
        remaining_args = args[2:] if len(args) > 2 else ()

        qubit_expandable = 0 in expandable_indices
        bit_expandable = 1 in expandable_indices

        if qubit_expandable and bit_expandable:
            expanded_qubits = self._expand_sgmq_arg(qubit_arg)
            expanded_bits = self._expand_sgmq_arg(bit_arg)

            if len(expanded_qubits) != len(expanded_bits):
                msg = (
                    f"SGMQ measure requires matching qubit and bit lengths: "
                    f"got {len(expanded_qubits)} qubits and {len(expanded_bits)} bits"
                )
                raise ValueError(msg)

            return [(qubit, bit, *remaining_args) for qubit, bit in zip(expanded_qubits, expanded_bits, strict=True)]
        if qubit_expandable:
            expanded_qubits = self._expand_sgmq_arg(qubit_arg)
            return [(qubit, bit_arg, *remaining_args) for qubit in expanded_qubits]
        if bit_expandable:
            expanded_bits = self._expand_sgmq_arg(bit_arg)
            return [(qubit_arg, bit, *remaining_args) for bit in expanded_bits]
        return [args]

    def to_circuit(self) -> Circuit:
        """Build the circuit.

        Returns:
            Circuit: The built circuit.

        """
        return Circuit(deepcopy(self.register_manager), deepcopy(self.ir))
