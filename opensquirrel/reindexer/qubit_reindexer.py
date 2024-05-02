from typing import List

from opensquirrel.circuit import Circuit
from opensquirrel.register_manager import RegisterManager
from opensquirrel.squirrel_ir import (
    BlochSphereRotation,
    ControlledGate,
    Gate,
    MatrixGate,
    Qubit,
    SquirrelIR,
    SquirrelIRVisitor,
)


class _QubitReIndexer(SquirrelIRVisitor):
    def __init__(self, qubit_indices: List[int]):
        self.qubit_indices = qubit_indices

    def visit_bloch_sphere_rotation(self, g: BlochSphereRotation):
        result = BlochSphereRotation(
            qubit=Qubit(self.qubit_indices.index(g.qubit.index)), angle=g.angle, axis=g.axis, phase=g.phase
        )
        return result

    def visit_matrix_gate(self, g: MatrixGate):
        mapped_operands = [Qubit(self.qubit_indices.index(op.index)) for op in g.operands]
        result = MatrixGate(matrix=g.matrix, operands=mapped_operands)
        return result

    def visit_controlled_gate(self, controlled_gate: ControlledGate):
        control_qubit = Qubit(self.qubit_indices.index(controlled_gate.control_qubit.index))
        target_gate = controlled_gate.target_gate.accept(self)
        result = ControlledGate(control_qubit=control_qubit, target_gate=target_gate)
        return result


def get_reindexed_circuit(replacement: List[Gate], qubit_indices: List[int]) -> Circuit:
    register_manager = RegisterManager(qubit_register_size=len(qubit_indices))
    replacement_ir = SquirrelIR()
    qubit_re_indexer = _QubitReIndexer(qubit_indices)
    for gate in replacement:
        gate_with_reindexed_qubits = gate.accept(qubit_re_indexer)
        replacement_ir.add_gate(gate_with_reindexed_qubits)

    return Circuit(register_manager, replacement_ir)
