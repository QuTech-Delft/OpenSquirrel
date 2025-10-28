from abc import ABC, abstractmethod
from typing import Any

import numpy as np

from opensquirrel.common import ATOL
from opensquirrel.ir.expression import Axis, AxisLike, Bit, BitLike, Expression, Qubit, QubitLike
from opensquirrel.ir.ir import IRVisitor
from opensquirrel.ir.semantics import BlochSphereRotation
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

    def accept(self, visitor: IRVisitor) -> Any:
        instruction_visit = visitor.visit_instruction(self)
        return instruction_visit if instruction_visit is not None else visitor.visit_non_unitary(self)


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
        return self.qubit, self.bit, self.axis

    def accept(self, visitor: IRVisitor) -> Any:
        non_unitary_visit = visitor.visit_non_unitary(self)
        return non_unitary_visit if non_unitary_visit is not None else visitor.visit_measure(self)

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
        non_unitary_visit = visitor.visit_non_unitary(self)
        return non_unitary_visit if non_unitary_visit is not None else visitor.visit_init(self)


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
        non_unitary_visit = visitor.visit_non_unitary(self)
        return non_unitary_visit if non_unitary_visit is not None else visitor.visit_reset(self)
