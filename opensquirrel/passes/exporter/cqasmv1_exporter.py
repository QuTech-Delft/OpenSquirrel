from __future__ import annotations

from typing import TYPE_CHECKING, Any, SupportsFloat, SupportsInt

from opensquirrel.exceptions import UnsupportedGateError
from opensquirrel.ir import (
    CNOT,
    CR,
    CZ,
    SWAP,
    Barrier,
    BsrWithAngleParam,
    BsrWithoutParams,
    ControlledGate,
    CRk,
    Float,
    Gate,
    Init,
    Int,
    IRVisitor,
    MatrixGate,
    Measure,
    Qubit,
    Reset,
    Wait,
)

if TYPE_CHECKING:
    from opensquirrel.circuit import Circuit
    from opensquirrel.register_manager import RegisterManager


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

    def visit_bloch_sphere_rotation(self, gate: Gate) -> None:
        raise UnsupportedGateError(gate)

    def visit_bsr_without_params(self, gate: BsrWithoutParams) -> None:
        qubit_operand = gate.qubit.accept(self)
        self.output += f"{gate.name.lower()} {qubit_operand}\n"

    def visit_bsr_with_angle_params(self, gate: BsrWithAngleParam) -> None:
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
        qubit_argument = measure.arguments[0].accept(self)  # type: ignore[index]
        self.output += f"measure_z {qubit_argument}\n"

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


def export(circuit: Circuit) -> str:
    cqasmv1_creator = _CQASMv1Creator(circuit.register_manager)

    circuit.ir.accept(cqasmv1_creator)

    # Remove all trailing lines and leave only one
    return cqasmv1_creator.output.rstrip() + "\n"
