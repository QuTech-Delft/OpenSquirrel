from typing import Any

from opensquirrel.ir import Bit, Gate, IRVisitor, Qubit, QubitLike
from opensquirrel.ir.expression import Expression
from opensquirrel.ir.semantics import BlochSphereRotation


class ControlledGate(Gate):
    def __init__(
        self, control_qubit: QubitLike, target_gate: BlochSphereRotation, name: str = "ControlledGate"
    ) -> None:
        Gate.__init__(self, name)
        self.control_qubit = Qubit(control_qubit)
        self.target_qubit = Qubit(target_gate.qubit)
        self.target_gate = target_gate

        if self._check_repeated_qubit_operands([self.control_qubit, self.target_qubit]):
            msg = "control and target qubit cannot be the same"
            raise ValueError(msg)

    def __repr__(self) -> str:
        return f"{self.name}(control_qubit={self.control_qubit}, target_gate={self.target_gate})"

    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_controlled_gate(self)

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return self.control_qubit, *self.target_gate.arguments

    def get_qubit_operands(self) -> list[Qubit]:
        return [self.control_qubit, self.target_qubit]

    def get_bit_operands(self) -> list[Bit]:
        return []

    def is_identity(self) -> bool:
        return self.target_gate.is_identity()
