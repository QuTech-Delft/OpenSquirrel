from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from opensquirrel.ir import (
    IR,
    Barrier,
    Gate,
    Init,
    IRVisitor,
    Measure,
    Reset,
    Wait,
)
from opensquirrel.ir.semantics import (
    BlochSphereRotation,
    BsrAngleParam,
    BsrFullParams,
    BsrNoParams,
    ControlledGate,
    MatrixGate,
)
from opensquirrel.register_manager import BitRegister, QubitRegister, RegisterManager

if TYPE_CHECKING:
    from opensquirrel import (
        CNOT,
        CR,
        CZ,
        SWAP,
        CRk,
    )
    from opensquirrel.circuit import Circuit


class _QubitReindexer(IRVisitor):
    """
    Reindex a whole IR.
    A new IR where the qubit indices are replaced by their positions in qubit indices.
    _E.g._, for mapping = [3, 1]:
    - Qubit(index=1) becomes Qubit(index=1), and
    - Qubit(index=3) becomes Qubit(index=0).

    Args:
        qubit_indices: a list of qubit indices, e.g. [3, 1]

    Returns:

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

    def visit_bloch_sphere_rotation(self, gate: BlochSphereRotation) -> BlochSphereRotation:
        return BlochSphereRotation(
            qubit=self.qubit_indices.index(gate.qubit.index),
            axis=gate.axis,
            angle=gate.angle,
            phase=gate.phase,
            name=gate.name,
        )

    def visit_bsr_no_params(self, gate: BsrNoParams) -> BlochSphereRotation:
        return self.visit_bloch_sphere_rotation(gate)

    def visit_bsr_full_params(self, gate: BsrFullParams) -> BlochSphereRotation:
        return self.visit_bloch_sphere_rotation(gate)

    def visit_bsr_angle_param(self, gate: BsrAngleParam) -> BlochSphereRotation:
        return self.visit_bloch_sphere_rotation(gate)

    def visit_matrix_gate(self, gate: MatrixGate) -> MatrixGate:
        reindexed_operands = [self.qubit_indices.index(op.index) for op in gate.operands]
        return MatrixGate(matrix=gate.matrix, operands=reindexed_operands)

    def visit_swap(self, gate: SWAP) -> MatrixGate:
        return self.visit_matrix_gate(gate)

    def visit_controlled_gate(self, gate: ControlledGate) -> ControlledGate:
        control_qubit = self.qubit_indices.index(gate.control_qubit.index)
        target_gate = gate.target_gate.accept(self)
        return ControlledGate(control_qubit=control_qubit, target_gate=target_gate)

    def visit_cnot(self, gate: CNOT) -> ControlledGate:
        return self.visit_controlled_gate(gate)

    def visit_cz(self, gate: CZ) -> ControlledGate:
        return self.visit_controlled_gate(gate)

    def visit_cr(self, gate: CR) -> ControlledGate:
        return self.visit_controlled_gate(gate)

    def visit_crk(self, gate: CRk) -> ControlledGate:
        return self.visit_controlled_gate(gate)


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
