from functools import cached_property
from typing import Any

import numpy as np

from opensquirrel.ir import Gate, IRVisitor, Qubit, QubitLike
from opensquirrel.ir.semantics import CanonicalGateSemantic, ControlledGateSemantic, MatrixGateSemantic
from opensquirrel.ir.semantics.bsr import bsr_from_matrix
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

    @cached_property
    def matrix(self) -> MatrixGateSemantic:
        if self._matrix:
            return self._matrix

        if self._controlled:
            self._matrix = MatrixGateSemantic(get_matrix(self, 2))
            return self._matrix

        if self._canonical:
            from opensquirrel.utils.matrix_expander import can1, can2

            if self._canonical.rotations:
                k1, k2, k3, k4 = (
                    can1(rotation.axis, rotation.angle, rotation.phase) for rotation in self._canonical.rotations
                )
                return MatrixGateSemantic(np.kron(k3, k4) @ can2(self._canonical.axis) @ np.kron(k1, k2))
            return MatrixGateSemantic(can2(self._canonical.axis))

        msg = f"invalid GateSemantic: {self.gate_semantic}"
        raise ValueError(msg)    

    @cached_property
    def canonical(self) -> CanonicalGateSemantic:
        if not self._canonical:           
            from opensquirrel.utils.matrix_expander import canonical_decomposition

            k1, k2, k3, k4, axis = canonical_decomposition(np.array(self.matrix))

            bsr1 = bsr_from_matrix(k1)
            bsr2 = bsr_from_matrix(k2)
            bsr3 = bsr_from_matrix(k3)
            bsr4 = bsr_from_matrix(k4)
            self._canonical = CanonicalGateSemantic(axis, [bsr1, bsr2, bsr3, bsr4])
        return self._canonical

    @cached_property
    def controlled(self) -> ControlledGateSemantic | None:        
        return self._controlled        

    @property
    def qubit_operands(self) -> tuple[Qubit, ...]:
        return (self.qubit0, self.qubit1)

    def accept(self, visitor: IRVisitor) -> Any:
        """Accepts visitor and processes this IR node."""
        visit_parent = super().accept(visitor)
        return visit_parent if visit_parent is not None else visitor.visit_two_qubit_gate(self)

    def is_identity(self) -> bool:
        """Checks if the two-qubit gate is an identity gate.

        Returns:
            True if the two-qubit gate is an identity gate, False otherwise.

        """
        if self.controlled:
            return self.controlled.is_identity()
        if self.matrix:
            return self.matrix.is_identity()
        if self.canonical:
            return self.canonical.is_identity()
        return False

    def __repr__(self) -> str:
        return f"TwoQubitGate(qubits=[{self.qubit0, self.qubit1}], gate_semantic={self.gate_semantic})"
