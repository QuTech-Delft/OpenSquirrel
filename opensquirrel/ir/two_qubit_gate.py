from opensquirrel.ir.semantics.bsr import bsr_from_matrix
from functools import cached_property
from typing import Any

import numpy as np

from opensquirrel.ir import Gate, IRVisitor, Qubit, QubitLike
from opensquirrel.ir.semantics import CanonicalGateSemantic, ControlledGateSemantic, MatrixGateSemantic, CanonicalAxis
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

        if self._check_repeated_qubit_operands(self.qubit_operands):
            msg = "qubit operands cannot be the same qubit"
            raise ValueError(msg)

    def __repr__(self) -> str:
        return f"TwoQubitGate(qubits=[{self.qubit0, self.qubit1}], gate_semantic={self.gate_semantic})"

    @cached_property
    def matrix(self) -> MatrixGateSemantic:
        if self._matrix:
            return self._matrix

        if self._controlled:
            self._matrix = MatrixGateSemantic(get_matrix(self, 2))
            return self._matrix

        if self._canonical:
            from opensquirrel.utils.matrix_expander import can2

            return MatrixGateSemantic(can2(self._canonical.axis))
        return MatrixGateSemantic(np.eye(4))

    @cached_property
    def canonical(self) -> CanonicalGateSemantic:
        if self._canonical:
            return self._canonical

        from opensquirrel.utils.matrix_expander import canonical_decomposition

        k1, k2, k3, k4, axis = canonical_decomposition(np.array(self.matrix))            
        self._canonical = CanonicalGateSemantic(axis, [k1, k2, k3, k4])
        return self._canonical

    @cached_property
    def controlled(self) -> ControlledGateSemantic | None:
        if self._controlled:
            return self._controlled

        if self._matrix:
            return None

        if self._canonical:
            matrix_4x4 = np.array(self.matrix)                
            return None
            # tx, ty, tz = self._canonical.axis
            # if (ty == 0 and tz == 0):
                
            #     bsr = bsr_from_matrix(matrix_4x4[2:, 2:])
            #     self._controlled = ControlledGateSemantic(bsr)
            #     return self._controlled
        return None

    def accept(self, visitor: IRVisitor) -> Any:
        visit_parent = super().accept(visitor)
        return visit_parent if visit_parent is not None else visitor.visit_two_qubit_gate(self)

    @property
    def qubit_operands(self) -> tuple[Qubit, ...]:
        return (self.qubit0, self.qubit1)

    def is_identity(self) -> bool:
        if self.controlled:
            return self.controlled.is_identity()
        if self.matrix:
            return self.matrix.is_identity()
        if self.canonical:
            return self.canonical.is_identity()
        return False
