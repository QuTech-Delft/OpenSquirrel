from opensquirrel.circuit import Circuit
from opensquirrel.ir import (
    IR,
    Barrier,
    IRVisitor,
    NonUnitary,
    Qubit,
    Wait,
)
from opensquirrel.ir.single_qubit_gate import SingleQubitGate
from opensquirrel.ir.two_qubit_gate import TwoQubitGate
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

    def visit_non_unitary(self, non_unitary: NonUnitary) -> NonUnitary:
        non_unitary.qubit.accept(self)
        return non_unitary

    def visit_barrier(self, barrier: Barrier) -> Barrier:
        barrier.qubit.accept(self)
        return barrier

    def visit_wait(self, wait: Wait) -> Wait:
        wait.qubit.accept(self)
        return wait

    def visit_single_qubit_gate(self, gate: SingleQubitGate) -> SingleQubitGate:
        gate.qubit.accept(self)
        return gate

    def visit_two_qubit_gate(self, gate: TwoQubitGate) -> TwoQubitGate:
        for operand in gate.get_qubit_operands():
            operand.accept(self)

        if gate.control is not None:
            gate.control.target_gate.qubit.accept(self)
        return gate


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
