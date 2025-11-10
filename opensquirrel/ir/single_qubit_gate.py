from __future__ import annotations
from typing import Any

from opensquirrel.ir import Gate, Qubit, QubitLike
from opensquirrel.ir.ir import IRVisitor
from opensquirrel.ir.semantics.bsr import BlochSphereRotation
from opensquirrel.ir.expression import Expression
from opensquirrel.ir.semantics.gate_semantic import MatrixSemantic


class SingleQubitGate(Gate):
    bsr: BlochSphereRotation
    matrix: MatrixSemantic | None = None

    def __init__(self, qubit: QubitLike) -> None:
        super().__init__()
        self.qubit = Qubit(qubit)


    @staticmethod
    def from_bsr(qubit: QubitLike, bsr: BlochSphereRotation) -> SingleQubitGate:
        gate = SingleQubitGate(qubit=qubit)
        gate.bsr = bsr
        return gate      

    def accept(self, visitor: IRVisitor) -> Any:
        return self.bsr.accept(visitor)

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return (self.qubit,)

    def get_qubit_operands(self) -> list[Qubit]:
        return [self.qubit]

    def is_identity(self) -> bool:
        if self.bsr is not None:
            return self.bsr.is_identity()
        return self.matrix.is_identity() if self.matrix else False