from __future__ import annotations

from itertools import groupby
from typing import TYPE_CHECKING, SupportsFloat, SupportsInt

from opensquirrel.exceptions import UnsupportedGateError
from opensquirrel.ir import Barrier, Float, Gate, Init, Int, IRVisitor, Measure, Qubit, Reset, Statement, Wait

if TYPE_CHECKING:
    from opensquirrel.circuit import Circuit
    from opensquirrel.register_manager import RegisterManager


class _CQASMv1Creator(IRVisitor):
    # Precision used when writing out a float number
    FLOAT_PRECISION = 8

    def __init__(self, register_manager: RegisterManager, barrier_links: list[list[Statement]]) -> None:
        self.register_manager = register_manager
        qubit_register_size = self.register_manager.get_qubit_register_size()
        self.output = "version 1.0\n\n{}\n\n".format(f"qubits {qubit_register_size}" if qubit_register_size > 0 else "")
        self.barrier_links = barrier_links

    def visit_qubit(self, qubit: Qubit) -> str:
        qubit_register_name = self.register_manager.get_qubit_register_name()
        return f"{qubit_register_name}[{qubit.index}]"

    def visit_int(self, i: SupportsInt) -> str:
        i = Int(i)
        return f"{i.value}"

    def visit_float(self, f: SupportsFloat) -> str:
        f = Float(f)
        return f"{f.value:.{self.FLOAT_PRECISION}}"

    def visit_measure(self, measure: Measure) -> None:
        qubit_argument = measure.arguments[0].accept(self)  # type: ignore[index]
        self.output += f"{measure.name}_z {qubit_argument}\n"

    def visit_init(self, init: Init) -> None:
        qubit_argument = init.arguments[0].accept(self)  # type: ignore[index]
        self.output += f"prep_z {qubit_argument}\n"

    def visit_reset(self, reset: Reset) -> None:
        qubit_argument = reset.arguments[0].accept(self)  # type: ignore[index]
        self.output += f"prep_z {qubit_argument}\n"

    def visit_barrier(self, barrier: Barrier) -> None:
        if self.barrier_links and barrier == self.barrier_links[0][-1]:
            qubit_register_name = self.register_manager.get_qubit_register_name()
            qubit_indices = [str(barrier.arguments[0].index) for barrier in self.barrier_links[0]]  # type: ignore
            self.output += f"barrier {qubit_register_name}[{', '.join(qubit_indices)}]\n"
            del self.barrier_links[0]

    def visit_wait(self, wait: Wait) -> None:
        qubit_argument = wait.arguments[0].accept(self)  # type: ignore[index]
        parameter = wait.arguments[1].accept(self)  # type: ignore[index]
        self.output += f"wait {qubit_argument}, {parameter}\n"

    def visit_gate(self, gate: Gate) -> None:
        gate_name = gate.name.lower()
        if gate.is_anonymous:
            raise UnsupportedGateError(gate)
        params = []
        if any(not isinstance(arg, Qubit) for arg in gate.arguments):  # type: ignore[union-attr]
            params = [arg.accept(self) for arg in gate.arguments if not isinstance(arg, Qubit)]  # type: ignore[union-attr]
        qubit_args = (arg.accept(self) for arg in gate.arguments if isinstance(arg, Qubit))  # type: ignore[union-attr]
        self.output += "{} {}{}\n".format(gate_name, ", ".join(qubit_args), ", " + ", ".join(params) if params else "")


def export(circuit: Circuit) -> str:
    barrier_links = [
        list(barrier_link)
        for barrier, barrier_link in groupby(circuit.ir.statements, lambda stmt: isinstance(stmt, Barrier))
        if barrier
    ]
    cqasmv1_creator = _CQASMv1Creator(circuit.register_manager, barrier_links)
    circuit.ir.accept(cqasmv1_creator)

    # Remove all trailing lines and leave only one
    return cqasmv1_creator.output.rstrip() + "\n"
