from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from opensquirrel.ir import (
    CNOT,
    CR,
    CZ,
    IR,
    SWAP,
    Barrier,
    BlochSphereRotation,
    BsrWithAngleParam,
    BsrWithoutParams,
    ControlledGate,
    CRk,
    Gate,
    Init,
    IRVisitor,
    MatrixGate,
    Measure,
    Reset,
    Wait,
)
from opensquirrel.register_manager import BitRegister, QubitRegister, RegisterManager

if TYPE_CHECKING:
    from opensquirrel.circuit import Circuit


class _QubitReindexer(IRVisitor):
    """
    Reindex a whole IR.

    Args:
        qubit_indices: a list of qubit indices, e.g. [3, 1]

    Returns:
         A new IR where the qubit indices are replaced by their positions in qubit indices.
         E.g., for mapping = [3, 1]:
         - Qubit(index=1) becomes Qubit(index=1), and
         - Qubit(index=3) becomes Qubit(index=0).
    """

    def __init__(self, qubit_indices: list[int]) -> None:
        self.qubit_indices = qubit_indices

    def visit_init(self, init: Init) -> Init:
        return Init(qubit=self.qubit_indices.index(init.qubit.index))

    def visit_measure(self, measure: Measure) -> Measure:
        return Measure(qubit=self.qubit_indices.index(measure.qubit.index), bit=measure.bit, axis=measure.axis)

    def visit_reset(self, reset: Reset) -> Reset:
        qubit_to_reset = self.qubit_indices.index(reset.qubit.index)
        return Reset(qubit=qubit_to_reset)

    def visit_barrier(self, barrier: Barrier) -> Barrier:
        return Barrier(qubit=self.qubit_indices.index(barrier.qubit.index))

    def visit_wait(self, wait: Wait) -> Wait:
        return Wait(qubit=self.qubit_indices.index(wait.qubit.index), time=wait.time)

    def visit_bloch_sphere_rotation(self, g: BlochSphereRotation) -> BlochSphereRotation:
        return BlochSphereRotation(
            qubit=self.qubit_indices.index(g.qubit.index),
            axis=g.axis,
            angle=g.angle,
            phase=g.phase,
            name=g.name,
        )

    def visit_bsr_without_params(self, g: BsrWithoutParams) -> BlochSphereRotation:
        return self.visit_bloch_sphere_rotation(g)

    def visit_bsr_with_angle_params(self, g: BsrWithAngleParam) -> BlochSphereRotation:
        return self.visit_bloch_sphere_rotation(g)

    def visit_matrix_gate(self, g: MatrixGate) -> MatrixGate:
        reindexed_operands = [self.qubit_indices.index(op.index) for op in g.operands]
        return MatrixGate(matrix=g.matrix, operands=reindexed_operands)

    def visit_swap(self, g: SWAP) -> MatrixGate:
        return self.visit_matrix_gate(g)

    def visit_controlled_gate(self, g: ControlledGate) -> ControlledGate:
        control_qubit = self.qubit_indices.index(g.control_qubit.index)
        target_gate = g.target_gate.accept(self)
        return ControlledGate(control_qubit=control_qubit, target_gate=target_gate)

    def visit_cnot(self, g: CNOT) -> ControlledGate:
        return self.visit_controlled_gate(g)

    def visit_cz(self, g: CZ) -> ControlledGate:
        return self.visit_controlled_gate(g)

    def visit_cr(self, g: CR) -> ControlledGate:
        return self.visit_controlled_gate(g)

    def visit_crk(self, g: CRk) -> ControlledGate:
        return self.visit_controlled_gate(g)


def get_reindexed_circuit(
    replacement_gates: Iterable[Gate],
    qubit_indices: list[int],
    bit_register_size: int = 0,
) -> Circuit:
    from opensquirrel.circuit import Circuit

    qubit_reindexer = _QubitReindexer(qubit_indices)
    qubit_register = QubitRegister(len(qubit_indices))
    bit_register = BitRegister(bit_register_size)
    register_manager = RegisterManager(qubit_register, bit_register)
    replacement_ir = IR()
    for gate in replacement_gates:
        gate_with_reindexed_qubits = gate.accept(qubit_reindexer)
        replacement_ir.add_gate(gate_with_reindexed_qubits)
    return Circuit(register_manager, replacement_ir)
