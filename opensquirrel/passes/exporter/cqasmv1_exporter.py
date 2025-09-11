from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, SupportsFloat, SupportsInt

from opensquirrel.exceptions import UnsupportedGateError
from opensquirrel.ir import (
    Barrier,
    Float,
    Gate,
    Init,
    Int,
    IRVisitor,
    Measure,
    Qubit,
    Reset,
    Wait,
)

if TYPE_CHECKING:
    from opensquirrel import (
        CNOT,
        CR,
        CZ,
        SWAP,
        CRk,
    )
    from opensquirrel.circuit import Circuit
    from opensquirrel.ir.semantics import (
        BlochSphereRotation,
        BsrAngleParam,
        BsrFullParams,
        BsrNoParams,
        ControlledGate,
        MatrixGate,
    )
    from opensquirrel.register_manager import RegisterManager


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

    def visit_gate(self, gate: Gate) -> None:
        raise UnsupportedGateError(gate)

    def visit_bloch_sphere_rotation(self, gate: BlochSphereRotation) -> None:
        raise UnsupportedGateError(gate)

    def visit_bsr_no_params(self, gate: BsrNoParams) -> None:
        qubit_operand = gate.qubit.accept(self)
        self.output += f"{gate.name.lower()} {qubit_operand}\n"

    def visit_bsr_full_params(self, gate: BsrFullParams) -> None:
        raise UnsupportedGateError(gate)

    def visit_bsr_angle_param(self, gate: BsrAngleParam) -> None:
        theta_argument = gate.theta.accept(self)
        qubit_operand = gate.qubit.accept(self)
        self.output += f"{gate.name.lower()} {qubit_operand}, {theta_argument}\n"

    def visit_matrix_gate(self, gate: MatrixGate) -> None:
        raise UnsupportedGateError(gate)

    def visit_swap(self, gate: SWAP) -> Any:
        qubit_operand_0 = gate.qubit_0.accept(self)
        qubit_operand_1 = gate.qubit_1.accept(self)
        self.output += f"swap {qubit_operand_0}, {qubit_operand_1}\n"

    def visit_controlled_gate(self, gate: ControlledGate) -> None:
        raise UnsupportedGateError(gate)

    def visit_cnot(self, gate: CNOT) -> None:
        control_qubit_operand = gate.control_qubit.accept(self)
        target_qubit_operand = gate.target_qubit.accept(self)
        self.output += f"cnot {control_qubit_operand}, {target_qubit_operand}\n"

    def visit_cz(self, gate: CZ) -> None:
        control_qubit_operand = gate.control_qubit.accept(self)
        target_qubit_operand = gate.target_qubit.accept(self)
        self.output += f"cz {control_qubit_operand}, {target_qubit_operand}\n"

    def visit_cr(self, gate: CR) -> None:
        control_qubit_operand = gate.control_qubit.accept(self)
        theta_argument = gate.theta.accept(self)
        target_qubit_operand = gate.target_qubit.accept(self)
        self.output += f"cr({theta_argument}) {control_qubit_operand}, {target_qubit_operand}\n"

    def visit_crk(self, gate: CRk) -> None:
        control_qubit_operand = gate.control_qubit.accept(self)
        k_argument = gate.k.accept(self)
        target_qubit_operand = gate.target_qubit.accept(self)
        self.output += f"crk({k_argument}) {control_qubit_operand}, {target_qubit_operand}\n"

    def visit_measure(self, measure: Measure) -> None:
        qubit_argument = measure.arguments[0].accept(self)
        self.output += f"measure_z {qubit_argument}\n"

    def visit_init(self, init: Init) -> None:
        qubit_argument = init.arguments[0].accept(self)
        self.output += f"prep_z {qubit_argument}\n"

    def visit_reset(self, reset: Reset) -> None:
        qubit_argument = reset.arguments[0].accept(self)
        self.output += f"prep_z {qubit_argument}\n"

    def visit_barrier(self, barrier: Barrier) -> None:
        qubit_argument = barrier.arguments[0].accept(self)
        self.output += f"barrier {qubit_argument}\n"

    def visit_wait(self, wait: Wait) -> None:
        qubit_argument = wait.arguments[0].accept(self)
        parameter = wait.arguments[1].accept(self)
        self.output += f"wait {qubit_argument}, {parameter}\n"


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
    barrier_index_match = re.search(r"\d+", line)
    if not barrier_index_match:
        msg = "expecting a barrier index but found none"
        raise CqasmV1ExporterParseError(msg)
    return int(barrier_index_match.group(0))


def export(circuit: Circuit) -> str:
    cqasmv1_creator = _CQASMv1Creator(circuit.register_manager)

    circuit.ir.accept(cqasmv1_creator)

    # Remove all trailing lines and leave only one
    return post_process(cqasmv1_creator.output).rstrip() + "\n"
