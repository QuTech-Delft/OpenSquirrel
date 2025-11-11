from typing import Any

from opensquirrel.ir import IRVisitor, Qubit, QubitLike
from opensquirrel.ir.expression import Expression
from opensquirrel.ir.single_qubit_gate import SingleQubitGate
from opensquirrel.ir.unitary import Gate


class ControlledGate(Gate):
    def __init__(self, control_qubit: QubitLike, target_gate: SingleQubitGate, name: str | None = None) -> None:
        Gate.__init__(self, name=name or "ControlledGate")
        self.control_qubit = Qubit(control_qubit)
        self.target_gate = target_gate
        self.target_qubit = Qubit(target_gate.qubit)

        if self._check_repeated_qubit_operands([self.control_qubit, self.target_qubit]):
            msg = "control and target qubit cannot be the same"
            raise ValueError(msg)

    def __repr__(self) -> str:
        return f"{self.name}(control_qubit={self.control_qubit}, target_gate={self.target_gate.bsr})"

    def accept(self, visitor: IRVisitor) -> Any:
        visit_parent = super().accept(visitor)
        return visit_parent if visit_parent is not None else visitor.visit_controlled_gate(self)

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return self.control_qubit, *self.target_gate.arguments

    def get_qubit_operands(self) -> list[Qubit]:
        return [self.control_qubit, self.target_qubit]

    def is_identity(self) -> bool:
        return self.target_gate.is_identity()
