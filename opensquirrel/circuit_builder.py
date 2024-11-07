from __future__ import annotations

import inspect
from collections.abc import Callable, Mapping
from copy import deepcopy
from functools import partial
from typing import Any

from typing_extensions import Self

from opensquirrel.circuit import Circuit
from opensquirrel.default_directives import default_directive_set
from opensquirrel.default_gates import default_gate_aliases, default_gate_set
from opensquirrel.default_measures import default_measure_set
from opensquirrel.default_resets import default_reset_set
from opensquirrel.instruction_library import DirectiveLibrary, GateLibrary, MeasureLibrary, ResetLibrary
from opensquirrel.ir import ANNOTATIONS_TO_TYPE_MAP, IR, Comment, Directive, Gate, Measure, Qubit, QubitLike, Reset
from opensquirrel.register_manager import BitRegister, QubitRegister, RegisterManager


class CircuitBuilder(GateLibrary, MeasureLibrary, ResetLibrary, DirectiveLibrary):
    """
    A class using the builder pattern to make construction of circuits easy from Python.
    Adds corresponding instruction when a method is called. Checks that instructions are known and called with the right
    arguments.
    Mainly here to allow for Qiskit-style circuit construction:

    Args:
        qubit_register_size (int): Size of the qubit register
        bit_register_size (int): Size of the bit register
        gate_set (list): Supported gates
        gate_aliases (dict): Supported gate aliases
        measure_set (list): Supported measure instructions

    Example:
        >>> CircuitBuilder(qubit_register_size=3, bit_register_size=3).\
        H(0).CNOT(0, 1).CNOT(0, 2).\
        to_circuit()
        version 3.
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
        gate_set: list[Callable[..., Gate]] = default_gate_set,
        gate_aliases: Mapping[str, Callable[..., Gate]] = default_gate_aliases,
        measure_set: list[Callable[..., Measure]] = default_measure_set,
        reset_set: list[Callable[..., Reset]] = default_reset_set,
        directive_set: list[Callable[..., Directive]] = default_directive_set,
    ) -> None:
        GateLibrary.__init__(self, gate_set, gate_aliases)
        MeasureLibrary.__init__(self, measure_set)
        ResetLibrary.__init__(self, reset_set)
        DirectiveLibrary.__init__(self, directive_set)
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
        if any(attr == measure.__name__ for measure in self.measure_set):
            generator_f_measure = MeasureLibrary.get_measure_f(self, attr)
            self._check_generator_f_args(generator_f_measure, attr, args)
            self.ir.add_measure(generator_f_measure(*args))
        elif any(attr == reset.__name__ for reset in self.reset_set):
            generator_f_reset = ResetLibrary.get_reset_f(self, attr)
            self._check_generator_f_args(generator_f_reset, attr, args)
            self.ir.add_reset(generator_f_reset(*args))
        elif any(attr == directive.__name__ for directive in self.directive_set):
            generator_f_directive = DirectiveLibrary.get_directive_f(self, attr)
            self._check_generator_f_args(generator_f_directive, attr, args)
            self.ir.add_directive(generator_f_directive(*args))
        else:
            generator_f_gate = GateLibrary.get_gate_f(self, attr)
            self._check_generator_f_args(generator_f_gate, attr, args)
            self.ir.add_gate(generator_f_gate(*args))
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
        generator_f: Callable[..., Gate | Measure | Reset | Directive],
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

            # fix for python39
            try:
                is_incorrect_type = not isinstance(args[i], expected_type)  # type: ignore
            except TypeError:
                # expected type is probably a Union, which works differently in python39
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
