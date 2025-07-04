import math

import numpy as np

from opensquirrel.ir import BlochSphereRotation, ControlledGate, MatrixGate
from opensquirrel.utils import get_matrix


def test_bloch_sphere_rotation() -> None:
    gate = BlochSphereRotation(qubit=0, axis=(0.8, -0.3, 1.5), angle=0.9468, phase=2.533)
    np.testing.assert_almost_equal(
        get_matrix(gate, 2),
        [
            [-0.50373461 + 0.83386635j, 0.05578802 + 0.21864595j, 0, 0],
            [0.18579927 + 0.12805072j, -0.95671077 + 0.18381011j, 0, 0],
            [0, 0, -0.50373461 + 0.83386635j, 0.05578802 + 0.21864595j],
            [0, 0, 0.18579927 + 0.12805072j, -0.95671077 + 0.18381011j],
        ],
    )


def test_controlled_gate() -> None:
    gate = ControlledGate(2, BlochSphereRotation(qubit=0, axis=(1, 0, 0), angle=math.pi, phase=math.pi / 2))
    np.testing.assert_almost_equal(
        get_matrix(gate, 3),
        [
            [1, 0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 1],
            [0, 0, 0, 0, 0, 0, 1, 0],
        ],
    )


def test_matrix_gate() -> None:
    gate = MatrixGate(
        [
            [1, 0, 0, 0],
            [0, 0, 1, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1],
        ],
        operands=[1, 2],
    )
    np.testing.assert_almost_equal(
        get_matrix(gate, 3),
        [
            [1, 0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 1, 0, 0],
            [0, 0, 1, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 0, 1],
        ],
    )
