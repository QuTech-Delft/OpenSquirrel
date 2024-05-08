from typing import List

from opensquirrel.circuit import Circuit
from opensquirrel.mapper.mapping import Mapping
from opensquirrel.register_manager import RegisterManager
from opensquirrel.squirrel_ir import (
    BlochSphereRotation,
    Comment,
    ControlledGate,
    Gate,
    MatrixGate,
    Measure,
    Qubit,
    SquirrelIR,
    SquirrelIRVisitor,
)


class _QubitReindexer(SquirrelIRVisitor):
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

    def __init__(self, qubit_indices: List[int]):
        self.qubit_indices = qubit_indices

    def visit_measure(self, measure: Measure):
        return Measure(qubit=Qubit(self.qubit_indices.index(measure.qubit.index)), axis=measure.axis)

    def visit_bloch_sphere_rotation(self, g: BlochSphereRotation):
        return BlochSphereRotation(
            qubit=Qubit(self.qubit_indices.index(g.qubit.index)), angle=g.angle, axis=g.axis, phase=g.phase
        )

    def visit_matrix_gate(self, g: MatrixGate):
        reindexed_operands = [Qubit(self.qubit_indices.index(op.index)) for op in g.operands]
        return MatrixGate(matrix=g.matrix, operands=reindexed_operands)

    def visit_controlled_gate(self, controlled_gate: ControlledGate):
        control_qubit = Qubit(self.qubit_indices.index(controlled_gate.control_qubit.index))
        target_gate = controlled_gate.target_gate.accept(self)
        return ControlledGate(control_qubit=control_qubit, target_gate=target_gate)


def get_reindexed_circuit(replacement_gates: List[Gate], qubit_indices: List[int]) -> Circuit:
    qubit_reindexer = _QubitReindexer(qubit_indices)
    register_manager = RegisterManager(qubit_register_size=len(qubit_indices))
    replacement_ir = SquirrelIR()
    for gate in replacement_gates:
        gate_with_reindexed_qubits = gate.accept(qubit_reindexer)
        replacement_ir.add_gate(gate_with_reindexed_qubits)
    return Circuit(register_manager, replacement_ir)
