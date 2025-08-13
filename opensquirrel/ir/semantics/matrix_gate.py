from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

import numpy as np
from numpy.typing import ArrayLike, DTypeLike

from opensquirrel.common import ATOL, repr_round
from opensquirrel.ir import Bit, Gate, Qubit, QubitLike

if TYPE_CHECKING:
    from opensquirrel.ir import IRVisitor
    from opensquirrel.ir.expression import Expression


class MatrixGate(Gate):
    def __init__(
        self, matrix: ArrayLike | list[list[int | DTypeLike]], operands: Iterable[QubitLike], name: str = "MatrixGate"
    ) -> None:
        Gate.__init__(self, name)
        self.operands = [Qubit(operand) for operand in operands]
        if len(self.operands) < 2:
            msg = "for 1q gates, please use BlochSphereRotation"
            raise ValueError(msg)

        if self._check_repeated_qubit_operands(self.operands):
            msg = "operands cannot be the same"
            raise ValueError(msg)

        matrix = np.asarray(matrix, dtype=np.complex128)

        expected_number_of_rows = 1 << len(self.operands)
        expected_number_of_cols = expected_number_of_rows
        if matrix.shape != (expected_number_of_rows, expected_number_of_cols):
            msg = (
                f"incorrect matrix shape. "
                f"Expected {(expected_number_of_rows, expected_number_of_cols)} but received {matrix.shape}"
            )
            raise ValueError(msg)

        self.matrix = matrix

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return tuple(self.operands)

    def __repr__(self) -> str:
        return f"{self.name}(qubits={self.operands}, matrix={repr_round(self.matrix)})"

    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_matrix_gate(self)

    def get_qubit_operands(self) -> list[Qubit]:
        return self.operands

    def get_bit_operands(self) -> list[Bit]:
        return []

    def is_identity(self) -> bool:
        return np.allclose(self.matrix, np.eye(2 ** len(self.operands)), atol=ATOL)
