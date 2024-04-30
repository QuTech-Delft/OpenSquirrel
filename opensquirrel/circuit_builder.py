from __future__ import annotations

import inspect
from functools import partial
from typing import TYPE_CHECKING, Any, Callable, Dict

from opensquirrel.circuit import Circuit
from opensquirrel.default_gates import default_gate_aliases, default_gate_set
from opensquirrel.instruction_library import GateLibrary
from opensquirrel.squirrel_ir import Comment, Gate, SquirrelIR

if TYPE_CHECKING:
    from typing import Self


class CircuitBuilder(GateLibrary):
    """
    A class using the builder pattern to make construction of circuits easy from Python.
    Adds corresponding gate when a method is called. Checks gates are known and called with the right arguments.
    Mainly here to allow for Qiskit-style circuit construction:

    Example:
        >>> CircuitBuilder(number_of_qubits=3).h(Qubit(0)).cnot(Qubit(0), Qubit(1)).cnot(Qubit(0), Qubit(2)). \
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

    _default_qubit_register_name = "q"

    def __init__(
        self,
        number_of_qubits: int,
        gate_set: list[Callable[..., Gate]] = default_gate_set,
        gate_aliases: Dict[str, Callable[..., Gate]] = default_gate_aliases,
    ):
        GateLibrary.__init__(self, gate_set, gate_aliases)
        self.squirrel_ir = SquirrelIR(
            number_of_qubits=number_of_qubits, qubit_register_name=self._default_qubit_register_name
        )

    def __getattr__(self, attr: Any) -> Callable[..., Self]:
        if attr == "comment":
            return self._add_comment

        return partial(self._add_this_gate, attr)

    def to_circuit(self) -> Circuit:
        return Circuit(self.squirrel_ir)

    def _add_comment(self, comment_string: str) -> Self:
        self.squirrel_ir.add_comment(Comment(comment_string))
        return self

    def _add_this_gate(self, attr: Any, *args: Any) -> Self:
        generator_f = GateLibrary.get_gate_f(self, attr)

        for i, par in enumerate(inspect.signature(generator_f).parameters.values()):
            if not isinstance(args[i], par.annotation):
                raise TypeError(
                    f"Wrong argument type for gate `{attr}`, got {type(args[i])} but expected {par.annotation}"
                )

        self.squirrel_ir.add_gate(generator_f(*args))
        return self
