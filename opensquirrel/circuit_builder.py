from __future__ import annotations

import inspect
from collections.abc import Callable
from copy import deepcopy
from functools import partial
from typing import Any

from typing_extensions import Self

from opensquirrel import instruction_library
from opensquirrel.circuit import Circuit
from opensquirrel.ir import (
    ANNOTATIONS_TO_TYPE_MAP,
    IR,
    Bit,
    BitLike,
    Instruction,
    Qubit,
    QubitLike,
    is_bit_like_annotation,
    is_qubit_like_annotation,
)
from opensquirrel.register_manager import BitRegister, QubitRegister, RegisterManager


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

    def __getattr__(self, attr: Any) -> Callable[..., Self]:
        return partial(self._add_instruction, attr)

    def _add_instruction(self, attr: str, *args: Any) -> Self:
        if attr in instruction_library.gate_set:
            generator_f_gate = instruction_library.get_gate_f(attr)
            self._check_generator_f_args(generator_f_gate, attr, args)
            self.ir.add_gate(generator_f_gate(*args))
        elif attr in instruction_library.non_unitary_set:
            generator_f_non_unitary = instruction_library.get_non_unitary_f(attr)
            self._check_generator_f_args(generator_f_non_unitary, attr, args)
            self.ir.add_non_unitary(generator_f_non_unitary(*args))
        else:
            msg = f"unknown instruction '{attr}'"
            raise ValueError(msg)
        return self

    def _check_qubit_out_of_bounds_access(self, qubit: QubitLike) -> None:
        """Throw error if qubit index is outside the qubit register range.

        Args:
            qubit: qubit to check.
        """
        index = Qubit(qubit).index
        if index >= self.register_manager.get_qubit_register_size():
            msg = "qubit index is out of bounds"
            raise IndexError(msg)

    def _check_bit_out_of_bounds_access(self, bit: BitLike) -> None:
        """Throw error if bit index is outside the bit register range.

        Args:
            bit: bit to check.
        """
        index = Bit(bit).index
        if index >= self.register_manager.get_bit_register_size():
            msg = "bit index is out of bounds"
            raise IndexError(msg)

    def _check_generator_f_args(
        self,
        generator_f: Callable[..., Instruction],
        attr: str,
        args: tuple[Any, ...],
    ) -> None:
        """General instruction validation function.
        The function checks if each instruction has the proper arguments
        and if the qubit and bits are within the register range.

        Args:
            generator_f: Instruction function
            attr: Type of instruction
            args: Arguments parsed into the function
        """
        for i, par in enumerate(inspect.signature(generator_f).parameters.values()):
            try:
                expected_type = (
                    ANNOTATIONS_TO_TYPE_MAP[par.annotation] if isinstance(par.annotation, str) else par.annotation
                )
            except KeyError as e:
                msg = "unknown annotation type"
                raise TypeError(msg) from e

            # Fix for Python 3.9
            try:
                is_incorrect_type = not isinstance(args[i], expected_type)  # type: ignore
            except TypeError:
                # Expected type is probably a Union, which works differently in Python 3.9
                is_incorrect_type = not isinstance(args[i], expected_type.__args__)  # type: ignore

            if is_incorrect_type:
                msg = f"wrong argument type for instruction `{attr}`, got {type(args[i])} but expected {expected_type}"
                raise TypeError(msg)
            if is_qubit_like_annotation(expected_type):
                self._check_qubit_out_of_bounds_access(args[i])
            elif is_bit_like_annotation(expected_type):
                self._check_bit_out_of_bounds_access(args[i])

    def to_circuit(self) -> Circuit:
        return Circuit(deepcopy(self.register_manager), deepcopy(self.ir))
