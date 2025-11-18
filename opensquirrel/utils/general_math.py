import cmath
import math

import numpy as np
from numpy.typing import NDArray


def acos(value: float) -> float:
    """Fix float approximations like 1.0000000000002, which acos does not like."""
    value = max(min(value, 1.0), -1.0)
    return math.acos(value)


def are_axes_consecutive(axis_a_index: int, axis_b_index: int) -> bool:
    """Check if axis 'a' immediately precedes axis 'b' (in a circular fashion [x, y, z, x...])."""
    return axis_a_index - axis_b_index in (-1, 2)


def matrix_from_u_gate_params(theta: float, phi: float, lmbda: float) -> NDArray[np.complex128]:
    """Convert the U-gate to a matrix using its parameters."""
    return np.array(
        [
            [math.cos(theta / 2), -cmath.exp(1j * lmbda) * math.sin(theta / 2)],
            [cmath.exp(1j * phi) * math.sin(theta / 2), cmath.exp(1j * (phi + lmbda)) * math.cos(theta / 2)],
        ],
        dtype=np.complex128,
    )
