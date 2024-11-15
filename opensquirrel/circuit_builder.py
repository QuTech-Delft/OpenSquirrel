from __future__ import annotations

import inspect
from collections.abc import Callable, Mapping
from copy import deepcopy
from functools import partial
from typing import Any

from typing_extensions import Self

from opensquirrel.circuit import Circuit
from opensquirrel.default_instructions import default_gate_set, default_non_gate_set
from opensquirrel.instruction_library import InstructionLibrary
from opensquirrel.ir import ANNOTATIONS_TO_TYPE_MAP, IR, Comment, Gate, Instruction, NonGate, Qubit, QubitLike
from opensquirrel.register_manager import BitRegister, QubitRegister, RegisterManager


class CircuitBuilder(InstructionLibrary):
    """
    A class using the builder pattern to make construction of circuits easy from Python.
    Adds corresponding instruction when a method is called. Checks that instructions are known and called with the right
    arguments.
    Mainly here to allow for Qiskit-style circuit construction:

    Args:
        qubit_register_size (int): Size of the qubit register
        bit_register_size (int): Size of the bit register
        gate_set (list): Supported gates
        non_gate_set (list): Supported non-gates

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

    def __init__(
        self,
        qubit_register_size: int,
        bit_register_size: int = 0,
        gate_set: Mapping[str, Callable[..., Gate]] = default_gate_set,
        non_gate_set: Mapping[str, Callable[..., NonGate]] = default_non_gate_set,
    ) -> None:
        InstructionLibrary.__init__(self, gate_set, non_gate_set)
        self.register_manager = RegisterManager(QubitRegister(qubit_register_size), BitRegister(bit_register_size))
        self.ir = IR()

    def __getattr__(self, attr: Any) -> Callable[..., Self]:
        if attr == "comment":
            return self._add_comment

        return partial(self._add_instruction, attr)

    def _add_comment(self, comment_string: str) -> Self:
        self.ir.add_comment(Comment(comment_string))
        return self

    def _add_instruction(self, attr: str, *args: Any) -> Self:
        if attr in self.gate_set:
            generator_f_gate = self.get_gate_f(attr)
            self._check_generator_f_args(generator_f_gate, attr, args)
            self.ir.add_gate(generator_f_gate(*args))
        elif attr in self.non_gate_set:
            generator_f_non_gate = self.get_non_gate_f(attr)
            self._check_generator_f_args(generator_f_non_gate, attr, args)
            self.ir.add_non_gate(generator_f_non_gate(*args))
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

    def _check_bit_out_of_bounds_access(self, index: int) -> None:
        """Throw error if bit index is outside the qubit register range.

        Args:
            index: bit index
        """
        if index >= self.register_manager.get_bit_register_size():
            msg = "bit index is out of bounds"
            raise IndexError(msg)

    def _check_generator_f_args(
        self,
        generator_f: Callable[..., Instruction],
        attr: str,
        args: tuple[Any, ...],
    ) -> None:
        """General instruction validation function. The function checks if each instruction has the proper arguments
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
            if expected_type in (QubitLike, Qubit):
                self._check_qubit_out_of_bounds_access(args[i])
            elif args[i].__class__.__name__ == "Bit":
                self._check_bit_out_of_bounds_access(args[i].index)

    def to_circuit(self) -> Circuit:
        return Circuit(deepcopy(self.register_manager), deepcopy(self.ir))
