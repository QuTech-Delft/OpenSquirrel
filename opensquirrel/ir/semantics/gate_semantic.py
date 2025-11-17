from abc import ABC, abstractmethod

import numpy as np
from numpy.typing import ArrayLike, DTypeLike, NDArray

from opensquirrel.common import ATOL


class GateSemantic(ABC):
    @abstractmethod
    def is_identity(self) -> bool:
        pass


class MatrixSemantic(GateSemantic):
    def __init__(self, matrix: ArrayLike | list[list[int | DTypeLike]]) -> None:
        self.matrix = np.asarray(matrix, dtype=np.complex128)

        number_of_rows, number_of_cols = self.matrix.shape
        if (number_of_cols != number_of_rows) and (number_of_cols & (number_of_cols - 1) != 0):
            msg = (
                f"incorrect matrix shape. Expected {(number_of_rows, number_of_cols)} but received {self.matrix.shape}"
            )
            raise ValueError(msg)

    def is_identity(self) -> bool:
        return np.allclose(self.matrix, np.eye(self.matrix.shape[0]), atol=ATOL)

    def __array__(self) -> NDArray[np.complex128]:
        return self.matrix
