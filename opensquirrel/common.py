import cmath
import math
from typing import Tuple

import numpy as np

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
    norm = math.sqrt(nx**2 + ny**2 + nz**2)
    assert norm > 0.00000001

    nx /= norm
    ny /= norm
    nz /= norm

    result = cmath.rect(1, phase) * (
        math.cos(angle / 2) * np.identity(2) - 1j * math.sin(angle / 2) * (nx * X + ny * Y + nz * Z)
    )

    return result
