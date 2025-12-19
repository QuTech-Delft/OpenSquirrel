from typing import Any

import numpy as np
from numpy.typing import ArrayLike, DTypeLike, NDArray

from opensquirrel.common import ATOL, repr_round
from opensquirrel.ir import IRVisitor
from opensquirrel.ir.semantics.gate_semantic import GateSemantic


class MatrixGateSemantic(GateSemantic):
    def __init__(self, matrix: ArrayLike | list[list[int | DTypeLike]]) -> None:
        self.matrix = np.asarray(matrix, dtype=np.complex128)

        number_of_rows, number_of_cols = self.matrix.shape
        if number_of_cols != number_of_rows:
            msg = (
                f"incorrect matrix shape. The number of rows should be equal to the number of columns, but"
                f"{number_of_rows=} and {number_of_cols=}. "
            )
            raise ValueError(msg)

        if number_of_cols & (number_of_cols - 1) != 0:
            msg = "incorrect matrix shape. The number of rows/columns should be a power of 2."
            raise ValueError(msg)

    def is_identity(self) -> bool:
        return np.allclose(self.matrix, np.eye(self.matrix.shape[0]), atol=ATOL)

    def __array__(self, *args: Any, **kwargs: Any) -> NDArray[np.complex128]:
        return np.asarray(self.matrix, *args, **kwargs)

    def __repr__(self) -> str:
        return f"MatrixGateSemantic(matrix={repr_round(self.matrix)})"

    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_matrix_gate_semantic(self)
