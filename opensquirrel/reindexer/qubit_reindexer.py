from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from opensquirrel.ir import IR, BlochSphereRotation, ControlledGate, Gate, IRVisitor, MatrixGate, Measure, Qubit, Reset
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

    def visit_reset(self, reset: Reset) -> Reset:
        qubit_to_reset = self.qubit_indices.index(reset.qubit.index)
        return Reset(qubit=Qubit(qubit_to_reset))

    def visit_measure(self, measure: Measure) -> Measure:
        return Measure(qubits=[Qubit(self.qubit_indices.index(measure.qubit.index)),], bit=measure.bit, axis=measure.axis)

    def visit_bloch_sphere_rotation(self, g: BlochSphereRotation) -> BlochSphereRotation:
        return BlochSphereRotation(
            qubit=Qubit(self.qubit_indices.index(g.qubit.index)),
            angle=g.angle,
            axis=g.axis,
            phase=g.phase,
        )

    def visit_matrix_gate(self, g: MatrixGate) -> MatrixGate:
        reindexed_operands = [Qubit(self.qubit_indices.index(op.index)) for op in g.operands]
        return MatrixGate(matrix=g.matrix, operands=reindexed_operands)

    def visit_controlled_gate(self, controlled_gate: ControlledGate) -> ControlledGate:
        control_qubit = Qubit(self.qubit_indices.index(controlled_gate.control_qubit.index))
        target_gate = controlled_gate.target_gate.accept(self)
        return ControlledGate(control_qubit=control_qubit, target_gate=target_gate)


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
