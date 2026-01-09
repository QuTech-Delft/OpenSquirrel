from abc import ABC, abstractmethod
from typing import Any, SupportsInt

from opensquirrel.ir.expression import Bit, Expression, Int, Qubit, QubitLike
from opensquirrel.ir.ir import IRVisitor
from opensquirrel.ir.statement import Instruction


class ControlInstruction(Instruction, ABC):
    def __init__(self, qubit: QubitLike, name: str) -> None:
        Instruction.__init__(self, name)
        self.qubit = Qubit(qubit)

    @property
    @abstractmethod
    def arguments(self) -> tuple[Expression, ...]:
        pass

    @property
    def qubit_operands(self) -> tuple[Qubit, ...]:
        return (self.qubit,)

    @property
    def bit_operands(self) -> tuple[Bit, ...]:
        return ()


class Barrier(ControlInstruction):
    def __init__(self, qubit: QubitLike) -> None:
        ControlInstruction.__init__(self, qubit=qubit, name="barrier")
        self.qubit = Qubit(qubit)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(qubit={self.qubit})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Barrier) and self.qubit == other.qubit

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return (self.qubit,)

    def accept(self, visitor: IRVisitor) -> Any:
        visitor.visit_control_instruction(self)
        return visitor.visit_barrier(self)


class Wait(ControlInstruction):
    def __init__(self, qubit: QubitLike, time: SupportsInt) -> None:
        ControlInstruction.__init__(self, qubit=qubit, name="wait")
        self.qubit = Qubit(qubit)
        self.time = Int(time)

    def __repr__(self) -> str:
        return f"{self.name}(qubit={self.qubit}, time={self.time})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Wait) and self.qubit == other.qubit and self.time == other.time

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return self.qubit, self.time

    def accept(self, visitor: IRVisitor) -> Any:
        visitor.visit_control_instruction(self)
        return visitor.visit_wait(self)
