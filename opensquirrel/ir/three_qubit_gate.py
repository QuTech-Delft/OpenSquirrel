from functools import cached_property
from typing import Any

from opensquirrel.ir import Gate, IRVisitor, Qubit, QubitLike
from opensquirrel.ir.semantics import MatrixGateSemantic
from opensquirrel.ir.semantics.gate_semantic import GateSemantic


class ThreeQubitGate(Gate):
    def __init__(
        self,
        qubit0: QubitLike,
        qubit1: QubitLike,
        qubit2: QubitLike,
        gate_semantic: GateSemantic,
        name: str = "ThreeQubitGate",
    ) -> None:
        Gate.__init__(self, name)
        self.qubit0 = Qubit(qubit0)
        self.qubit1 = Qubit(qubit1)
        self.qubit2 = Qubit(qubit2)

        # A three-qubit gate can only be described by a matrix. ControlledGateSemantic describes a
        # single control qubit acting on a Bloch sphere rotation, and CanonicalGateSemantic
        # describes the canonical decomposition of a two-qubit gate.
        self._matrix = gate_semantic if isinstance(gate_semantic, MatrixGateSemantic) else None
        self.gate_semantic = gate_semantic

        if self._check_repeated_qubit_operands(self.qubit_operands):
            msg = "qubit operands cannot be the same qubit"
            raise ValueError(msg)

    @cached_property
    def matrix(self) -> MatrixGateSemantic:
        if self._matrix:
            return self._matrix

        msg = f"invalid gate semantic: {self.gate_semantic}"
        raise ValueError(msg)

    @property
    def qubit_operands(self) -> tuple[Qubit, ...]:
        return (self.qubit0, self.qubit1, self.qubit2)

    def accept(self, visitor: IRVisitor) -> Any:
        """Accepts visitor and processes this IR node."""
        visit_parent = super().accept(visitor)
        return visit_parent if visit_parent is not None else visitor.visit_three_qubit_gate(self)

    def is_identity(self) -> bool:
        """Checks if the three-qubit gate is an identity gate.

        Returns:
            True if the three-qubit gate is an identity gate, False otherwise.

        """
        return self.matrix.is_identity()

    def __repr__(self) -> str:
        return f"ThreeQubitGate(qubits=[{self.qubit0, self.qubit1, self.qubit2}], gate_semantic={self.gate_semantic})"
