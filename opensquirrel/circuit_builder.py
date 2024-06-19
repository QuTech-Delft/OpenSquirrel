from __future__ import annotations

import inspect
from collections.abc import Callable, Mapping
from functools import partial
from typing import Any

from typing_extensions import Self

from opensquirrel.circuit import Circuit
from opensquirrel.default_gates import default_gate_aliases, default_gate_set
from opensquirrel.default_measurements import default_measurement_set
from opensquirrel.instruction_library import GateLibrary, MeasurementLibrary
from opensquirrel.ir import IR, Comment, Gate, Measure
from opensquirrel.register_manager import RegisterManager


class CircuitBuilder(GateLibrary, MeasurementLibrary):
    """
    A class using the builder pattern to make construction of circuits easy from Python.
    Adds corresponding instruction when a method is called. Checks that instructions are known and called with the right
    arguments.
    Mainly here to allow for Qiskit-style circuit construction:

    Args:
        qubit_register_size (int): Size of the qubit register
        gate_set (list): Supported gates
        gate_aliases (dict): Supported gate aliases
        measurement_set (list): Supported measure instructions

    Example:
        >>> CircuitBuilder(qubit_register_size=3).H(Qubit(0)).CNOT(Qubit(0), Qubit(1)).CNOT(Qubit(0), Qubit(2)). \
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
        gate_set: list[Callable[..., Gate]] = default_gate_set,
        gate_aliases: Mapping[str, Callable[..., Gate]] = default_gate_aliases,
        measurement_set: list[Callable[..., Measure]] = default_measurement_set,
    ):
        GateLibrary.__init__(self, gate_set, gate_aliases)
        MeasurementLibrary.__init__(self, measurement_set)
        self.register_manager = RegisterManager(qubit_register_size)
        self.ir = IR()

    def __getattr__(self, attr: Any) -> Callable[..., Self]:
        if attr == "comment":
            return self._add_comment

        return partial(self._add_instruction, attr)

    def _add_comment(self, comment_string: str) -> Self:
        self.ir.add_comment(Comment(comment_string))
        return self

    def _add_instruction(self, attr: str, *args: Any) -> Self:
        if any(attr == measure.__name__ for measure in self.measurement_set):
            generator_f_measure = MeasurementLibrary.get_measurement_f(self, attr)
            self._check_generator_f_args(generator_f_measure, attr, args)
            self.ir.add_measurement(generator_f_measure(*args))
        else:
            generator_f_gate = GateLibrary.get_gate_f(self, attr)
            self._check_generator_f_args(generator_f_gate, attr, args)
            self.ir.add_gate(generator_f_gate(*args))
        return self

    @staticmethod
    def _check_generator_f_args(generator_f: Callable[..., Gate | Measure], attr: str, args: tuple[Any, ...]) -> None:
        for i, par in enumerate(inspect.signature(generator_f).parameters.values()):
            if isinstance(par.annotation, str):
                if args[i].__class__.__name__ != par.annotation:
                    raise TypeError(
                        f"Wrong argument type for instruction `{attr}`, got {type(args[i])} but expected {par.annotation}"
                    )
            elif not isinstance(args[i], par.annotation):
                raise TypeError(
                    f"Wrong argument type for instruction `{attr}`, got {type(args[i])} but expected {par.annotation}"
                )

    def to_circuit(self) -> Circuit:
        return Circuit(self.register_manager, self.ir)
