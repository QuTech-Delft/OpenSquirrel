from typing import List

from opensquirrel.circuit import Circuit
from opensquirrel.ir import (
    IR,
    BlochSphereRotation,
    Comment,
    ControlledGate,
    Gate,
    IRVisitor,
    MatrixGate,
    Measure,
    Qubit,
)
from opensquirrel.mapper.mapping import Mapping


class _QubitRemapper(IRVisitor):
    """
    Remap a whole IR.

    Args:
        mapping: a list of qubit indices, e.g. [3, 1, 0, 2]

    Returns:
         A new IR where the qubit indices are replaced by the values passed in mapping.
         E.g., for mapping = [3, 1, 0, 2]:
         - Qubit(index=0) becomes Qubit(index=3),
         - Qubit(index=1) becomes Qubit(index=1),
         - Qubit(index=2) becomes Qubit(index=0), and
         - Qubit(index=3) becomes Qubit(index=2).
    """

    def __init__(self, mapping: Mapping):
        self.mapping = mapping

    def visit_comment(self, comment: Comment):
        return comment

    def visit_qubit(self, qubit: Qubit):
        qubit.index = self.mapping[qubit.index]
        return qubit

    def visit_measure(self, measure: Measure):
        measure.qubit.accept(self)
        return measure

    def visit_bloch_sphere_rotation(self, g: BlochSphereRotation):
        g.qubit.accept(self)
        return g

    def visit_matrix_gate(self, g: MatrixGate):
        [op.accept(self) for op in g.operands]
        return g

    def visit_controlled_gate(self, controlled_gate: ControlledGate):
        controlled_gate.control_qubit.accept(self)
        controlled_gate.target_gate.accept(self)
        return controlled_gate


def get_remapped_ir(circuit: Circuit, mapping: Mapping) -> IR:
    assert len(mapping) <= circuit.qubit_register_size
    qubit_remapper = _QubitRemapper(mapping)
    replacement_ir = circuit.ir
    for statement in replacement_ir.statements:
        statement.accept(qubit_remapper)
    return replacement_ir


def remap_ir(circuit: Circuit, mapping: Mapping) -> None:
    assert len(mapping) <= circuit.qubit_register_size
    qubit_remapper = _QubitRemapper(mapping)
    for statement in circuit.ir.statements:
        statement.accept(qubit_remapper)
