from __future__ import annotations

from typing import TYPE_CHECKING

from opensquirrel.exceptions import UnsupportedGateError
from opensquirrel.ir import Comment, Float, Gate, Int, IRVisitor, Measure, Qubit, Reset

if TYPE_CHECKING:
    from opensquirrel.circuit import Circuit
    from opensquirrel.register_manager import RegisterManager


class _CQASMv1Creator(IRVisitor):
    # Precision used when writing out a float number
    FLOAT_PRECISION = 8

    def __init__(self, register_manager: RegisterManager) -> None:
        self.register_manager = register_manager
        qubit_register_size = self.register_manager.get_qubit_register_size()
        self.cqasmv1_string = "version 1.0\n\n{}\n\n".format(
            f"qubits {qubit_register_size}" if qubit_register_size > 0 else ""
        )

    def visit_qubit(self, qubit: Qubit) -> str:
        qubit_register_name = self.register_manager.get_qubit_register_name()
        return f"{qubit_register_name}[{qubit.index}]"

    def visit_int(self, i: Int) -> str:
        return f"{i.value}"

    def visit_float(self, f: Float) -> str:
        return f"{f.value:.{self.FLOAT_PRECISION}}"

    def visit_measure(self, measure: Measure) -> None:
        qubit_argument = measure.arguments[0].accept(self)  # type: ignore[index]
        self.cqasmv1_string += f"{measure.name}_z {qubit_argument}\n"

    def visit_reset(self, reset: Reset) -> None:
        qubit_argument = reset.arguments[0].accept(self)  # type: ignore[index]
        self.cqasmv1_string += f"prep_z {qubit_argument}\n"

    def visit_gate(self, gate: Gate) -> None:
        gate_name = gate.name.lower()
        if gate.is_anonymous:
            raise UnsupportedGateError(gate)
        params = []
        if any(
            not isinstance(arg, Qubit) for arg in gate.arguments
        ):  # type: ignore[union-attr]
            params = [
                arg.accept(self) for arg in gate.arguments if not isinstance(arg, Qubit)
            ]  # type: ignore[union-attr]
        qubit_args = (
            arg.accept(self) for arg in gate.arguments if isinstance(arg, Qubit)
        )  # type: ignore[union-attr]
        self.cqasmv1_string += "{} {}{}\n".format(
            gate_name, ", ".join(qubit_args), ", " + ", ".join(params) if params else ""
        )

    def visit_comment(self, comment: Comment) -> None:
        self.cqasmv1_string += f"\n/* {comment.str} */\n\n"


def export(circuit: Circuit) -> str:
    cqasmv1_creator = _CQASMv1Creator(circuit.register_manager)

    circuit.ir.accept(cqasmv1_creator)

    # remove all trailing lines and leave only one
    return cqasmv1_creator.cqasmv1_string.rstrip() + "\n"
