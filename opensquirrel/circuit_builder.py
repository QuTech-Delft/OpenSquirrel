import inspect
from typing import Callable, Dict

from opensquirrel.circuit import Circuit
from opensquirrel.default_gates import default_gate_aliases, default_gate_set
from opensquirrel.default_measurements import default_measurement_set
from opensquirrel.instruction_library import GateLibrary, MeasurementLibrary
from opensquirrel.squirrel_ir import Comment, Gate, Qubit, SquirrelIR


class CircuitBuilder(GateLibrary, MeasurementLibrary):
    """
    A class using the builder pattern to make construction of circuits easy from Python.
    Adds corresponding instruction when a method is called. Checks that instructions are known and called with the right
    arguments.
    Mainly here to allow for Qiskit-style circuit construction:

    Args:
        number_of_qubits (int): Number of qubits in the circuit
        gate_set (list): Supported gates
        gate_aliases (dict): Supported gate aliases
        measurement_set (list): Supported measure instructions

    Example:
        >>> CircuitBuilder(number_of_qubits=3).H(Qubit(0)).CNOT(Qubit(0), Qubit(1)).CNOT(Qubit(0), Qubit(2)). \
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
        number_of_qubits: int,
        gate_set: [Callable[..., Gate]] = default_gate_set,
        gate_aliases: Dict[str, Callable[..., Gate]] = default_gate_aliases,
        measurement_set: [Callable[..., Gate]] = default_measurement_set,
    ):
        GateLibrary.__init__(self, gate_set, gate_aliases)
        MeasurementLibrary.__init__(self, measurement_set)
        self.squirrel_ir = SquirrelIR(
            number_of_qubits=number_of_qubits, qubit_register_name="q"
        )

    def __getattr__(self, attr):
        def add_comment(comment_string: str):
            self.squirrel_ir.add_comment(Comment(comment_string))
            return self

        def add_instruction(*args):
            if any(attr == measure.__name__ for measure in self.measurement_set):
                generator_f = MeasurementLibrary.get_measurement_f(self, attr)
                _check_generator_f_args(generator_f, args)
                self.squirrel_ir.add_measurement(generator_f(*args))
            else:
                generator_f = GateLibrary.get_gate_f(self, attr)
                _check_generator_f_args(generator_f, args)
                self.squirrel_ir.add_gate(generator_f(*args))
            return self

        def _check_generator_f_args(generator_f, args):
            for i, par in enumerate(inspect.signature(generator_f).parameters.values()):
                if not isinstance(args[i], par.annotation):
                    raise TypeError(
                        f"Wrong argument type for instruction `{attr}`, got {type(args[i])} but expected"
                        f" {par.annotation}")

        return add_comment if attr == "comment" else add_instruction

    def to_circuit(self) -> Circuit:
        return Circuit(self.squirrel_ir)
