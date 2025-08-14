from __future__ import annotations

from math import tau
from typing import TYPE_CHECKING, SupportsFloat

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    from opensquirrel.ir.expression import Axis


ATOL = 0.000_000_1
REPR_DECIMALS = 5


def normalize_angle(x: SupportsFloat) -> float:
    r"""Normalize the angle to be in between the range of $(-\pi, \pi]$.

    Args:
        x: value to normalize.

    Returns:
        The normalized angle.
    """
    x = float(x)
    t = x - tau * (x // tau + 1)
    if t < -tau / 2 + ATOL:
        t += tau
    elif t > tau / 2:
        t -= tau
    return t


def are_matrices_equivalent_up_to_global_phase(
    matrix_a: NDArray[np.complex128], matrix_b: NDArray[np.complex128]
) -> bool:
    """Checks whether two matrices are equivalent up to a global phase.

    Args:
        matrix_a: first matrix.
        matrix_b: second matrix.

    Returns:
        Whether two matrices are equivalent up to a global phase.
    """
    first_non_zero = next(
        (i, j) for i in range(matrix_a.shape[0]) for j in range(matrix_a.shape[1]) if abs(matrix_a[i, j]) > ATOL
    )

    if abs(matrix_b[first_non_zero]) < ATOL:
        return False

    phase_difference = matrix_a[first_non_zero] / matrix_b[first_non_zero]

    return np.allclose(matrix_a, phase_difference * matrix_b, atol=ATOL)


def is_identity_matrix_up_to_a_global_phase(matrix: NDArray[np.complex128]) -> bool:
    """Checks whether matrix is an identity matrix up to a global phase.

    Args:
        matrix: matrix to check.
    Returns:
        Whether matrix is an identity matrix up to a global phase.
    """
    return are_matrices_equivalent_up_to_global_phase(matrix, np.eye(matrix.shape[0], dtype=np.complex128))


def repr_round(value: float | Axis | NDArray[np.complex128], decimals: int = REPR_DECIMALS) -> str:
    """
    Given a numerical value (of type `float`, `Axis`, or `NDArray[np.complex128]`):
    - rounds it to `REPR_DECIMALS`,
    - converts it to string, and
    - removes the newlines.

    Returns:
        A single-line string representation of a numerical value.
    """
    return f"{np.round(value, decimals)}".replace("\n", "")
