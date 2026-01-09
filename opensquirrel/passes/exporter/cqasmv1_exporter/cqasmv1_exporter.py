from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, SupportsFloat, SupportsInt

import numpy as np

from opensquirrel.common import ATOL, repr_round
from opensquirrel.default_instructions import default_two_qubit_gate_set
from opensquirrel.exceptions import UnsupportedGateError
from opensquirrel.ir import (
    Barrier,
    Float,
    Init,
    Int,
    IRVisitor,
    Measure,
    Qubit,
    Reset,
    Wait,
)
from opensquirrel.ir.semantics import (
    BsrAngleParam,
    BsrNoParams,
    BsrUnitaryParams,
    MatrixGateSemantic,
)
from opensquirrel.passes.exporter.general_exporter import Exporter

if TYPE_CHECKING:
    from opensquirrel.circuit import Circuit
    from opensquirrel.ir.single_qubit_gate import SingleQubitGate
    from opensquirrel.ir.two_qubit_gate import TwoQubitGate
    from opensquirrel.register_manager import RegisterManager


class CqasmV1Exporter(Exporter):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def export(self, circuit: Circuit) -> str:
        cqasmv1_creator = _CQASMv1Creator(circuit.register_manager)

        circuit.ir.accept(cqasmv1_creator)

        return _post_process(cqasmv1_creator.output).rstrip() + "\n"


class CqasmV1ExporterParseError(Exception):
    pass


class _CQASMv1Creator(IRVisitor):
    # Precision used when writing out a float number
    FLOAT_PRECISION = 8

    def __init__(self, register_manager: RegisterManager) -> None:
        self.register_manager = register_manager
        qubit_register_size = self.register_manager.get_qubit_register_size()
        self.output = "version 1.0{}\n\n".format(f"\n\nqubits {qubit_register_size}" if qubit_register_size > 0 else "")

    def visit_qubit(self, qubit: Qubit) -> str:
        qubit_register_name = self.register_manager.get_qubit_register_name()
        return f"{qubit_register_name}[{qubit.index}]"

    def visit_int(self, i: SupportsInt) -> str:
        i = Int(i)
        return f"{i.value}"

    def visit_float(self, f: SupportsFloat) -> str:
        f = Float(f)
        return f"{f.value:.{self.FLOAT_PRECISION}}"

    def visit_single_qubit_gate(self, gate: SingleQubitGate) -> Any:
        qubit_operand = gate.qubit.accept(self)

        match gate.bsr:
            case BsrNoParams():
                self.output += f"{gate.name.lower()} {qubit_operand}\n"

            case BsrAngleParam():
                theta_argument = gate.bsr.theta.accept(self)
                self.output += f"{gate.name.lower()} {qubit_operand}, {theta_argument}\n"

            case BsrUnitaryParams():
                matrix_repr = self.visit_matrix_gate_semantic(gate.matrix)
                self.output += f"{gate.name.lower()} {qubit_operand}, {matrix_repr}\n"

            case _:
                raise UnsupportedGateError(gate)

    def visit_two_qubit_gate(self, gate: TwoQubitGate) -> Any:
        if gate.name not in default_two_qubit_gate_set:
            raise UnsupportedGateError(gate)

        qubit_operand_0 = gate.qubit0.accept(self)
        qubit_operand_1 = gate.qubit1.accept(self)

        if gate.arguments:
            arguments = ", ".join(arg.accept(self) for arg in gate.arguments)
            self.output += f"{gate.name.lower()}({arguments}) {qubit_operand_0}, {qubit_operand_1}\n"
        else:
            self.output += f"{gate.name.lower()} {qubit_operand_0}, {qubit_operand_1}\n"

    def visit_measure(self, measure: Measure) -> None:
        qubit_argument = measure.qubit_operands[0].accept(self)
        self.output += f"measure_z {qubit_argument}\n"

    def visit_init(self, init: Init) -> None:
        qubit_argument = init.qubit_operands[0].accept(self)
        self.output += f"prep_z {qubit_argument}\n"

    def visit_reset(self, reset: Reset) -> None:
        qubit_argument = reset.qubit_operands[0].accept(self)
        self.output += f"prep_z {qubit_argument}\n"

    def visit_barrier(self, barrier: Barrier) -> None:
        qubit_argument = barrier.qubit_operands[0].accept(self)
        self.output += f"barrier {qubit_argument}\n"

    def visit_wait(self, wait: Wait) -> None:
        qubit_argument = wait.qubit_operands[0].accept(self)
        parameter = wait.arguments[0].accept(self)
        self.output += f"wait {qubit_argument}, {parameter}\n"

    def visit_matrix_gate_semantic(self, matrix: MatrixGateSemantic) -> Any:
        mat = np.array(matrix)
        elements: list[str] = [_convert_complex_number(mat[i, j]) for i in range(2) for j in range(2)]
        return f"[{elements[0]}, {elements[1]}; {elements[2]}, {elements[3]}]"


def _convert_complex_number(number: np.complex128) -> str:
    real_part = repr_round(number.real) if abs(number.real) > ATOL else ""
    imag_part = repr_round(abs(number.imag)) if abs(number.imag) > ATOL else ""
    if imag_part:
        sign = "+" if number.imag >= 0 else "-"
        sign = "" if not real_part and sign == "+" else sign
        imag_part = f"{sign}{imag_part} * im"
    result = f"{real_part}{imag_part}"
    return result or "0.0"


def _post_process(output: str) -> str:
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
    barrier_index_match = re.search(r"\d+", line)
    if not barrier_index_match:
        msg = "expecting a barrier index but found none"
        raise CqasmV1ExporterParseError(msg)
    return int(barrier_index_match.group(0))
