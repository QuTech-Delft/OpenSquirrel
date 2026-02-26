from __future__ import annotations

from typing import TYPE_CHECKING, Any

from opensquirrel.ir.semantics.gate_semantic import GateSemantic

if TYPE_CHECKING:
    from opensquirrel.ir import IRVisitor
    from opensquirrel.ir.single_qubit_gate import BlochSphereRotation


class ControlledGateSemantic(GateSemantic):
    def __init__(self, target_bsr: BlochSphereRotation) -> None:
        self.target_bsr = target_bsr

    def accept(self, visitor: IRVisitor) -> Any:
        """Accepts visitor and processes this IR node."""
        return visitor.visit_controlled_gate_semantic(self)

    def is_identity(self) -> bool:
        """Checks if the controlled gate semantic represents an identity operation.

        Returns:
            True if the controlled gate semantic represents an identity operation, False otherwise.

        """
        return self.target_bsr.is_identity()

    def __repr__(self) -> str:
        return f"ControlledGateSemantic(target_bsr={self.target_bsr})"

    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_controlled_gate_semantic(self)
