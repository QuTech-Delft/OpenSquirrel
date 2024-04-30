import inspect
from typing import Callable, Dict

from opensquirrel.circuit import Circuit
from opensquirrel.default_gates import default_gate_aliases, default_gate_set
from opensquirrel.gate_library import GateLibrary
from opensquirrel.squirrel_ir import Comment, Gate, Qubit, SquirrelIR


class CircuitBuilder(GateLibrary):
    """
    A class using the builder pattern to make construction of circuits easy from Python.
    Adds corresponding gate when a method is called. Checks gates are known and called with the right arguments.
    Mainly here to allow for Qiskit-style circuit construction:

    >>> CircuitBuilder(qubit_register_size=3).h(Qubit(0)).cnot(Qubit(0), Qubit(1)).cnot(Qubit(0), Qubit(2)).to_circuit()
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
    ):
        GateLibrary.__init__(self, gate_set, gate_aliases)
        self.register_manager = RegisterManager(qubit_register_size)
        self.squirrel_ir = SquirrelIR()

    def __getattr__(self, attr):
        def add_comment(comment_string: str):
            self.squirrel_ir.add_comment(Comment(comment_string))
            return self

        def add_this_gate(*args):
            generator_f = GateLibrary.get_gate_f(self, attr)

            for i, par in enumerate(inspect.signature(generator_f).parameters.values()):
                if not isinstance(args[i], par.annotation):
                    raise TypeError(
                        f"Wrong argument type for gate `{attr}`, got {type(args[i])} but expected {par.annotation}"
                    )

            self.squirrel_ir.add_gate(generator_f(*args))
            return self

        return add_comment if attr == "comment" else add_this_gate

    def to_circuit(self) -> Circuit:
        return Circuit(self.register_manager, self.squirrel_ir)
