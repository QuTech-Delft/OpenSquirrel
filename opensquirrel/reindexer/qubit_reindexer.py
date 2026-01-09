from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, OrderedDict

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
from opensquirrel.ir.semantics import ControlledGateSemantic
from opensquirrel.ir.single_qubit_gate import SingleQubitGate
from opensquirrel.ir.two_qubit_gate import TwoQubitGate
from opensquirrel.register_manager import (
    BIT_REGISTER_NAME,
    QUBIT_REGISTER_NAME,
    BitRegister,
    QubitRegister,
    RegisterManager,
)

if TYPE_CHECKING:
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

    def visit_single_qubit_gate(self, gate: SingleQubitGate) -> SingleQubitGate:
        gate.qubit.accept(self)
        return SingleQubitGate(qubit=self.qubit_indices.index(gate.qubit.index), gate_semantic=gate.bsr)

    def visit_two_qubit_gate(self, gate: TwoQubitGate) -> TwoQubitGate:
        qubit0 = self.qubit_indices.index(gate.qubit0.index)
        qubit1 = self.qubit_indices.index(gate.qubit1.index)

        if gate.controlled:
            target_gate = gate.controlled.target_gate.accept(self)
            return TwoQubitGate(qubit0=qubit0, qubit1=qubit1, gate_semantic=ControlledGateSemantic(target_gate))

        return TwoQubitGate(qubit0=qubit0, qubit1=qubit1, gate_semantic=gate.gate_semantic)


def get_reindexed_circuit(
    replacement_gates: Iterable[Gate],
    qubit_indices: list[int],
    bit_register_size: int = 0,
) -> Circuit:
    from opensquirrel.circuit import Circuit

    qubit_reindexer = _QubitReindexer(qubit_indices)
    register_manager = RegisterManager(
        OrderedDict({QUBIT_REGISTER_NAME: QubitRegister(len(qubit_indices))}),
        OrderedDict({BIT_REGISTER_NAME: BitRegister(bit_register_size)}),
    )
    replacement_ir = IR()
    for gate in replacement_gates:
        gate_with_reindexed_qubits = gate.accept(qubit_reindexer)
        replacement_ir.add_gate(gate_with_reindexed_qubits)
    return Circuit(register_manager, replacement_ir)
