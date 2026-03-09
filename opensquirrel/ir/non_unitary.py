from abc import ABC
from typing import Any

import numpy as np

from opensquirrel.common import ATOL
from opensquirrel.ir.expression import Axis, AxisLike, Bit, BitLike, Expression, Qubit, QubitLike
from opensquirrel.ir.ir import IRVisitor
from opensquirrel.ir.statement import Instruction


class NonUnitary(Instruction, ABC):
    def __init__(self, qubit: QubitLike, name: str) -> None:
        Instruction.__init__(self, name)
        self.qubit = Qubit(qubit)

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return ()

    @property
    def qubit_operands(self) -> tuple[Qubit, ...]:
        return (self.qubit,)

    @property
    def bit_operands(self) -> tuple[Bit, ...]:
        return ()

    def accept(self, visitor: IRVisitor) -> Any:
        """Accepts visitor and processes this IR node."""
        return visitor.visit_non_unitary(self)

    def __repr__(self) -> str:
        if self.arguments:
            args = ", ".join(f"{arg.__class__.__name__.lower()}={arg}" for arg in self.arguments)
            return f"{self.__class__.__name__}(qubit={self.qubit}, {args})"
        return f"{self.__class__.__name__}(qubit={self.qubit})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and self.qubit == other.qubit


class Measure(NonUnitary):
    def __init__(self, qubit: QubitLike, bit: BitLike, axis: AxisLike = (0, 0, 1)) -> None:
        NonUnitary.__init__(self, qubit=qubit, name="measure")
        self.bit = Bit(bit)
        self.axis = Axis(axis)

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return self.bit, self.axis

    @property
    def bit_operands(self) -> tuple[Bit, ...]:
        return (self.bit,)

    def accept(self, visitor: IRVisitor) -> Any:
        """Accepts visitor and processes this IR node."""
        non_unitary_visit = super().accept(visitor)
        return non_unitary_visit if non_unitary_visit is not None else visitor.visit_measure(self)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Measure) and self.qubit == other.qubit and np.allclose(self.axis, other.axis, atol=ATOL)
        )


class Init(NonUnitary):
    def __init__(self, qubit: QubitLike) -> None:
        NonUnitary.__init__(self, qubit=qubit, name="init")

    def accept(self, visitor: IRVisitor) -> Any:
        """Accepts visitor and processes this IR node."""
        non_unitary_visit = super().accept(visitor)
        return non_unitary_visit if non_unitary_visit is not None else visitor.visit_init(self)


class Reset(NonUnitary):
    def __init__(self, qubit: QubitLike) -> None:
        NonUnitary.__init__(self, qubit=qubit, name="reset")

    def accept(self, visitor: IRVisitor) -> Any:
        """Accepts visitor and processes this IR node."""
        non_unitary_visit = super().accept(visitor)
        return non_unitary_visit if non_unitary_visit is not None else visitor.visit_reset(self)
