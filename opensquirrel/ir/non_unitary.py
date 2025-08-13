from abc import ABC, abstractmethod
from typing import Any, SupportsInt

import numpy as np

from opensquirrel.common import ATOL
from opensquirrel.ir.expression import Axis, AxisLike, Bit, BitLike, Expression, Int, Qubit, QubitLike
from opensquirrel.ir.ir import IRVisitor
from opensquirrel.ir.statement import Instruction


class NonUnitary(Instruction, ABC):
    def __init__(self, qubit: QubitLike, name: str) -> None:
        Instruction.__init__(self, name)
        self.qubit = Qubit(qubit)

    @property
    @abstractmethod
    def arguments(self) -> tuple[Expression, ...]:
        pass

    def get_qubit_operands(self) -> list[Qubit]:
        return [self.qubit]

    def get_bit_operands(self) -> list[Bit]:
        return []


class Measure(NonUnitary):
    def __init__(self, qubit: QubitLike, bit: BitLike, axis: AxisLike = (0, 0, 1)) -> None:
        NonUnitary.__init__(self, qubit=qubit, name="measure")
        self.qubit = Qubit(qubit)
        self.bit = Bit(bit)
        self.axis = Axis(axis)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(qubit={self.qubit}, bit={self.bit}, axis={self.axis})"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Measure) and self.qubit == other.qubit and np.allclose(self.axis, other.axis, atol=ATOL)
        )

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return self.qubit, self.bit

    def accept(self, visitor: IRVisitor) -> Any:
        visitor.visit_non_unitary(self)
        return visitor.visit_measure(self)

    def get_bit_operands(self) -> list[Bit]:
        return [self.bit]


class Init(NonUnitary):
    def __init__(self, qubit: QubitLike) -> None:
        NonUnitary.__init__(self, qubit=qubit, name="init")
        self.qubit = Qubit(qubit)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(qubit={self.qubit})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Init) and self.qubit == other.qubit

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return (self.qubit,)

    def accept(self, visitor: IRVisitor) -> Any:
        visitor.visit_non_unitary(self)
        return visitor.visit_init(self)


class Reset(NonUnitary):
    def __init__(self, qubit: QubitLike) -> None:
        NonUnitary.__init__(self, qubit=qubit, name="reset")
        self.qubit = Qubit(qubit)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(qubit={self.qubit})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Reset) and self.qubit == other.qubit

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return (self.qubit,)

    def accept(self, visitor: IRVisitor) -> Any:
        visitor.visit_non_unitary(self)
        return visitor.visit_reset(self)


class Barrier(NonUnitary):
    def __init__(self, qubit: QubitLike) -> None:
        NonUnitary.__init__(self, qubit=qubit, name="barrier")
        self.qubit = Qubit(qubit)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(qubit={self.qubit})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Barrier) and self.qubit == other.qubit

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return (self.qubit,)

    def accept(self, visitor: IRVisitor) -> Any:
        visitor.visit_non_unitary(self)
        return visitor.visit_barrier(self)


class Wait(NonUnitary):
    def __init__(self, qubit: QubitLike, time: SupportsInt) -> None:
        NonUnitary.__init__(self, qubit=qubit, name="wait")
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
        visitor.visit_non_unitary(self)
        return visitor.visit_wait(self)
