from functools import cached_property
from typing import Any

import numpy as np

from opensquirrel.ir import Gate, IRVisitor, Qubit, QubitLike
from opensquirrel.ir.expression import Expression
from opensquirrel.ir.semantics import CanonicalGateSemantic, ControlledGateSemantic, MatrixGateSemantic
from opensquirrel.ir.semantics.gate_semantic import GateSemantic
from opensquirrel.utils import get_matrix


class TwoQubitGate(Gate):
    def __init__(
        self, qubit0: QubitLike, qubit1: QubitLike, gate_semantic: GateSemantic, name: str = "TwoQubitGate"
    ) -> None:
        Gate.__init__(self, name)
        self.qubit0 = Qubit(qubit0)
        self.qubit1 = Qubit(qubit1)

        self._controlled = gate_semantic if isinstance(gate_semantic, ControlledGateSemantic) else None
        self._matrix = gate_semantic if isinstance(gate_semantic, MatrixGateSemantic) else None
        self._canonical = gate_semantic if isinstance(gate_semantic, CanonicalGateSemantic) else None
        self.gate_semantic = gate_semantic

        if self._controlled and (self.qubit1 != self._controlled.target_gate.qubit):
            msg = "the qubit from the target gate does not match with 'qubit1'."
            raise ValueError(msg)

        if self._check_repeated_qubit_operands([self.qubit0, self.qubit1]):
            msg = "qubit0 and qubit1 cannot be the same"
            raise ValueError(msg)

    def __repr__(self) -> str:
        return f"TwoQubitGate(qubits=[{self.qubit0, self.qubit1}], gate_semantic={self.gate_semantic})"

    @cached_property
    def matrix(self) -> MatrixGateSemantic:
        if self._matrix:
            return self._matrix

        if self.controlled:
            self._matrix = MatrixGateSemantic(get_matrix(self, 2))
            return self._matrix

        if self.canonical:
            from opensquirrel.utils.matrix_expander import can2

            return MatrixGateSemantic(can2(self.canonical.axis))
        return MatrixGateSemantic(np.eye(4))

    @cached_property
    def canonical(self) -> CanonicalGateSemantic | None:
        return self._canonical

    @cached_property
    def controlled(self) -> ControlledGateSemantic | None:
        return self._controlled

    def accept(self, visitor: IRVisitor) -> Any:
        visit_parent = super().accept(visitor)
        return visit_parent if visit_parent is not None else visitor.visit_two_qubit_gate(self)

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return (self.qubit0, self.qubit1)

    def get_qubit_operands(self) -> list[Qubit]:
        return [self.qubit0, self.qubit1]

    def is_identity(self) -> bool:
        if self.controlled:
            return self.controlled.is_identity()
        if self.matrix:
            return self.matrix.is_identity()
        if self.canonical:
            return self.canonical.is_identity()
        return False
