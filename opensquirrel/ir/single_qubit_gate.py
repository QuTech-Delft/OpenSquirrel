from __future__ import annotations

from typing import TYPE_CHECKING, Any

from opensquirrel.ir import Gate, Qubit, QubitLike

if TYPE_CHECKING:
    from opensquirrel.ir.expression import Expression
    from opensquirrel.ir.ir import IRVisitor
    from opensquirrel.ir.semantics.bsr import BlochSphereRotation
    from opensquirrel.ir.semantics.gate_semantic import MatrixSemantic


class SingleQubitGate(Gate):
    bsr: BlochSphereRotation
    matrix: MatrixSemantic | None = None

    def __init__(self, qubit: QubitLike, name: str) -> None:
        Gate.__init__(self, name)
        self.qubit = Qubit(qubit)

    @staticmethod
    def from_bsr(qubit: QubitLike, bsr: BlochSphereRotation) -> SingleQubitGate:
        gate = SingleQubitGate(qubit=qubit, name="BlochSphereRotation")
        gate.bsr = bsr

        from opensquirrel.ir.default_gates.single_qubit_gates import try_match_replace_with_default_gate

        return try_match_replace_with_default_gate(gate)

    def accept(self, visitor: IRVisitor) -> Any:
        visit_gate = super().accept(visitor)
        return visit_gate if visit_gate is not None else visitor.visit_single_qubit_gate(self)

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return (self.qubit,)

    def get_qubit_operands(self) -> list[Qubit]:
        return [self.qubit]

    def is_identity(self) -> bool:
        if self.bsr is not None:
            return self.bsr.is_identity()
        return self.matrix.is_identity() if self.matrix else False
