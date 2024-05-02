import cmath
import math
import numpy as np
from typing import Tuple

ATOL = 0.0000001


def normalize_angle(x: float) -> float:
    t = x - 2 * math.pi * (x // (2 * math.pi) + 1)
    if t < -math.pi + ATOL:
        t += 2 * math.pi
    elif t > math.pi:
        t -= 2 * math.pi
    return t


def normalize_axis(axis: np.ndarray):
    norm = np.linalg.norm(axis)
    axis /= norm
    return axis


X = np.array([[0, 1], [1, 0]])
Y = np.array([[0, -1j], [1j, 0]])
Z = np.array([[1, 0], [0, -1]])


def can1(axis: Tuple[float, float, float], angle: float, phase: float = 0) -> np.ndarray:
    nx, ny, nz = axis
    norm = math.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
    assert norm > 0.00000001

    nx /= norm
    ny /= norm
    nz /= norm

    result = cmath.rect(1, phase) * (
        math.cos(angle / 2) * np.identity(2) - 1j * math.sin(angle / 2) * (nx * X + ny * Y + nz * Z)
    )

    return result


def are_matrices_equivalent_up_to_global_phase(matrix_a: np.ndarray, matrix_b: np.ndarray) -> bool:
    first_non_zero = next(
        (i, j) for i in range(matrix_a.shape[0]) for j in range(matrix_a.shape[1]) if abs(matrix_a[i, j]) > ATOL
    )

    if abs(matrix_b[first_non_zero]) < ATOL:
        return False

    phase_difference = matrix_a[first_non_zero] / matrix_b[first_non_zero]

    return np.allclose(matrix_a, phase_difference * matrix_b)
