from __future__ import annotations

from typing import TYPE_CHECKING

from opensquirrel.ir import GateSemantic

if TYPE_CHECKING:
    from opensquirrel.ir.single_qubit_gate import SingleQubitGate


class ControlledGateSemantic(GateSemantic):
    def __init__(self, target_gate: SingleQubitGate) -> None:
        self.target_gate = target_gate

    def is_identity(self) -> bool:
        return self.target_gate.is_identity()

    def __repr__(self) -> str:
        from opensquirrel.default_instructions import default_gate_set

        if self.target_gate.name in default_gate_set:
            return f"ControlledGateSemantic(target_gate={self.target_gate.name}(qubit={self.target_gate.qubit.index}))"
        return (
            f"ControlledGateSemantic(target_gate={self.target_gate.name}"
            f"(qubit={self.target_gate.qubit.index}, bsr={self.target_gate.bsr}))"
        )
