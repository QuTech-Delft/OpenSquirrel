from opensquirrel.circuit import Circuit
from opensquirrel.ir import (
    IR,
    Barrier,
    BlochSphereRotation,
    ControlledGate,
    Init,
    IRVisitor,
    MatrixGate,
    Measure,
    Qubit,
    Reset,
    Wait,
)
from opensquirrel.passes.mapper.mapping import Mapping


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

    def __init__(self, mapping: Mapping) -> None:
        self.mapping = mapping

    def visit_qubit(self, qubit: Qubit) -> Qubit:
        qubit.index = self.mapping[qubit.index]
        return qubit

    def visit_measure(self, measure: Measure) -> Measure:
        measure.qubit.accept(self)
        return measure

    def visit_init(self, init: Init) -> Init:
        init.qubit.accept(self)
        return init

    def visit_reset(self, reset: Reset) -> Reset:
        reset.qubit.accept(self)
        return reset

    def visit_barrier(self, barrier: Barrier) -> Barrier:
        barrier.qubit.accept(self)
        return barrier

    def visit_wait(self, wait: Wait) -> Wait:
        wait.qubit.accept(self)
        return wait

    def visit_bloch_sphere_rotation(self, g: BlochSphereRotation) -> BlochSphereRotation:
        g.qubit.accept(self)
        return g

    def visit_matrix_gate(self, g: MatrixGate) -> MatrixGate:
        for op in g.operands:
            op.accept(self)
        return g

    def visit_controlled_gate(self, controlled_gate: ControlledGate) -> ControlledGate:
        controlled_gate.control_qubit.accept(self)
        controlled_gate.target_gate.accept(self)
        return controlled_gate


def get_remapped_ir(circuit: Circuit, mapping: Mapping) -> IR:
    if len(mapping) > circuit.qubit_register_size:
        msg = "mapping is larger than the qubit register size"
        raise ValueError(msg)
    qubit_remapper = _QubitRemapper(mapping)
    replacement_ir = circuit.ir
    for statement in replacement_ir.statements:
        statement.accept(qubit_remapper)
    return replacement_ir


def remap_ir(circuit: Circuit, mapping: Mapping) -> None:
    if len(mapping) > circuit.qubit_register_size:
        msg = "mapping is larger than the qubit register size"
        raise ValueError(msg)
    qubit_remapper = _QubitRemapper(mapping)
    for statement in circuit.ir.statements:
        statement.accept(qubit_remapper)
