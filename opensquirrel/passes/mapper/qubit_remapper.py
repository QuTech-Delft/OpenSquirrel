from opensquirrel import (
    CNOT,
    CR,
    CZ,
    SWAP,
    CRk,
)
from opensquirrel.circuit import Circuit
from opensquirrel.ir import (
    IR,
    Barrier,
    Init,
    IRVisitor,
    Measure,
    Qubit,
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
from opensquirrel.passes.mapper.mapping import Mapping


class _QubitRemapper(IRVisitor):
    """
    Remap a whole IR.

    A new IR where the qubit indices are replaced by the values passed in mapping.
    _E.g._, for mapping = [3, 1, 0, 2]:
    - Qubit(index=0) becomes Qubit(index=3),
    - Qubit(index=1) becomes Qubit(index=1),
    - Qubit(index=2) becomes Qubit(index=0), and
    - Qubit(index=3) becomes Qubit(index=2).

    Args:
        mapping: a list of qubit indices, _e.g._, [3, 1, 0, 2]

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

    def visit_bloch_sphere_rotation(self, bloch_sphere_rotation: BlochSphereRotation) -> BlochSphereRotation:
        bloch_sphere_rotation.qubit.accept(self)
        return bloch_sphere_rotation

    def visit_bsr_no_params(self, gate: BsrNoParams) -> BlochSphereRotation:
        return self.visit_bloch_sphere_rotation(gate)

    def visit_bsr_full_params(self, gate: BsrFullParams) -> BlochSphereRotation:
        return self.visit_bloch_sphere_rotation(gate)

    def visit_bsr_angle_param(self, gate: BsrAngleParam) -> BlochSphereRotation:
        return self.visit_bloch_sphere_rotation(gate)

    def visit_matrix_gate(self, matrix_gate: MatrixGate) -> MatrixGate:
        for operand in matrix_gate.operands:
            operand.accept(self)
        return matrix_gate

    def visit_swap(self, gate: SWAP) -> MatrixGate:
        return self.visit_matrix_gate(gate)

    def visit_controlled_gate(self, controlled_gate: ControlledGate) -> ControlledGate:
        controlled_gate.control_qubit.accept(self)
        self.visit_bloch_sphere_rotation(controlled_gate.target_gate)
        return controlled_gate

    def visit_cnot(self, gate: CNOT) -> ControlledGate:
        return self.visit_controlled_gate(gate)

    def visit_cz(self, gate: CZ) -> ControlledGate:
        return self.visit_controlled_gate(gate)

    def visit_cr(self, gate: CR) -> ControlledGate:
        return self.visit_controlled_gate(gate)

    def visit_crk(self, gate: CRk) -> ControlledGate:
        return self.visit_controlled_gate(gate)


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
