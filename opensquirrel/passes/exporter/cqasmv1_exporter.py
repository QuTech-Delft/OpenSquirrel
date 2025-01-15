from __future__ import annotations

import re
from typing import TYPE_CHECKING, SupportsFloat, SupportsInt

from opensquirrel.exceptions import UnsupportedGateError
from opensquirrel.ir import Barrier, Float, Gate, Init, Int, IRVisitor, Measure, Qubit, Reset, Wait

if TYPE_CHECKING:
    from opensquirrel.circuit import Circuit
    from opensquirrel.register_manager import RegisterManager


class CqasmV1ExporterParseError(Exception):
    pass


class _CQASMv1Creator(IRVisitor):
    # Precision used when writing out a float number
    FLOAT_PRECISION = 8

    def __init__(self, register_manager: RegisterManager) -> None:
        self.register_manager = register_manager
        qubit_register_size = self.register_manager.get_qubit_register_size()
        self.output = "version 1.0\n\n{}\n\n".format(f"qubits {qubit_register_size}" if qubit_register_size > 0 else "")

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
        qubit_argument = barrier.arguments[0].accept(self)  # type: ignore[index]
        self.output += f"barrier {qubit_argument}\n"

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


def post_process(output: str) -> str:
    return _merge_barrier_groups(output)


def _merge_barrier_groups(output: str) -> str:
    ret: str = ""
    barrier_group_indices: list[int] = []
    for line in output.split("\n"):
        if not line.startswith("barrier"):
            if barrier_group_indices:
                ret += _dump_barrier_group(barrier_group_indices)
                barrier_group_indices = []
            ret += f"{line}\n"
        else:
            barrier_group_indices.append(_get_barrier_index(line))
    return ret


def _dump_barrier_group(indices: list[int]) -> str:
    return "barrier q[{}]\n".format(", ".join(map(str, indices)) if len(indices) != 0 else "")


def _get_barrier_index(line: str) -> int:
    barrier_index_match = re.search("\d+", line)
    if not barrier_index_match:
        msg = "expecting a barrier index but found none"
        raise CqasmV1ExporterParseError(msg)
    return int(barrier_index_match.group(0))


def export(circuit: Circuit) -> str:
    cqasmv1_creator = _CQASMv1Creator(circuit.register_manager)

    circuit.ir.accept(cqasmv1_creator)

    # Remove all trailing lines and leave only one
    return post_process(cqasmv1_creator.output).rstrip() + "\n"
