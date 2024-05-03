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
        qubit_indices: a list of the new indices, e.g. [3, 1, 0, 2]

    Returns:
         A new IR where the qubit indices are replaced by the values passed in qubit_indices.
         E.g., for qubit_indices = [3, 1, 0, 2]:
         - Qubit(index=0) becomes Qubit(index=3),
         - Qubit(index=1) becomes Qubit(index=1),
         - Qubit(index=2) becomes Qubit(index=0), and
         - Qubit(index=3) becomes Qubit(index=2).
    """
    def __init__(self, qubit_indices: List[int]):
        self.qubit_indices = qubit_indices

    def visit_comment(self, comment: Comment):
        return comment

    def visit_bloch_sphere_rotation(self, g: BlochSphereRotation):
        return BlochSphereRotation(
            qubit=Qubit(self.qubit_indices.index(g.qubit.index)), angle=g.angle, axis=g.axis, phase=g.phase
        )

    def visit_matrix_gate(self, g: MatrixGate):
        reindexed_operands = [Qubit(self.qubit_indices.index(op.index)) for op in g.operands]
        result = MatrixGate(matrix=g.matrix, operands=reindexed_operands)
        return result

    def visit_controlled_gate(self, controlled_gate: ControlledGate):
        control_qubit = Qubit(self.qubit_indices.index(controlled_gate.control_qubit.index))
        target_gate = controlled_gate.target_gate.accept(self)
        result = ControlledGate(control_qubit=control_qubit, target_gate=target_gate)
        return result

    def visit_measure(self, measure: Measure):
        return Measure(
            qubit=Qubit(self.qubit_indices.index(measure.qubit.index)), axis=measure.axis
        )


def get_reindexed_circuit(replacement_gates: List[Gate], qubit_indices: List[int]) -> Circuit:
    qubit_reindexer = _QubitReindexer(qubit_indices)
    register_manager = RegisterManager(qubit_register_size=len(qubit_indices))
    replacement_ir = SquirrelIR()
    for gate in replacement_gates:
        gate_with_reindexed_qubits = gate.accept(qubit_reindexer)
        replacement_ir.add_gate(gate_with_reindexed_qubits)
    return Circuit(register_manager, replacement_ir)


def reindex_circuit(circuit: Circuit, mapping: Mapping) -> None:
    qubit_reindexer = _QubitReindexer(mapping.values())
    replacement_ir = SquirrelIR()
    for statement in circuit.squirrel_ir.statements:
        statement = statement.accept(qubit_reindexer)
        replacement_ir.statements.append(statement)
    circuit.squirrel_ir = replacement_ir
