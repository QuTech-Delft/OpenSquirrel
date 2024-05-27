from __future__ import annotations

import inspect
from typing import Callable, Dict

from opensquirrel.circuit import Circuit
from opensquirrel.default_gates import default_gate_aliases, default_gate_set
from opensquirrel.default_measurements import default_measurement_set
from opensquirrel.instruction_library import GateLibrary, MeasurementLibrary
from opensquirrel.ir import IR, Comment, Gate, Qubit
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
        gate_set: [Callable[..., Gate]] = default_gate_set,
        gate_aliases: Dict[str, Callable[..., Gate]] = default_gate_aliases,
        measurement_set: List[Callable[..., Measure]] = default_measurement_set,
    ):
        GateLibrary.__init__(self, gate_set, gate_aliases)
        MeasurementLibrary.__init__(self, measurement_set)
        self.register_manager = RegisterManager(qubit_register_size)
        self.ir = IR()

    def __getattr__(self, attr):
        def add_comment(comment_string: str) -> CircuitBuilder:
            self.ir.add_comment(Comment(comment_string))
            return self

        def add_instruction(*args: tuple) -> CircuitBuilder:
            if any(attr == measure.__name__ for measure in self.measurement_set):
                generator_f = MeasurementLibrary.get_measurement_f(self, attr)
                _check_generator_f_args(generator_f, args)
                self.ir.add_measurement(generator_f(*args))
            else:
                generator_f = GateLibrary.get_gate_f(self, attr)
                _check_generator_f_args(generator_f, args)
                self.ir.add_gate(generator_f(*args))
            return self

        def _check_generator_f_args(generator_f, args):
            for i, par in enumerate(inspect.signature(generator_f).parameters.values()):
                if not isinstance(args[i], par.annotation):
                    raise TypeError(
                        f"Wrong argument type for instruction `{attr}`, got {type(args[i])} but expected"
                        f" {par.annotation}"
                    )

        return add_comment if attr == "comment" else add_instruction

    def to_circuit(self) -> Circuit:
        return Circuit(self.register_manager, self.ir)
