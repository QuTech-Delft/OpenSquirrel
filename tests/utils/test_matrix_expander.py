from math import pi, sqrt
from typing import Any

import numpy as np
import pytest
from numpy.typing import NDArray

from opensquirrel.ir import AxisLike
from opensquirrel.ir.semantics import (
    BlochSphereRotation,
    CanonicalGateSemantic,
    ControlledGateSemantic,
    MatrixGateSemantic,
)
from opensquirrel.ir.single_qubit_gate import SingleQubitGate
from opensquirrel.ir.two_qubit_gate import TwoQubitGate
from opensquirrel.utils import get_matrix


def test_bloch_sphere_rotation() -> None:
    gate = SingleQubitGate(0, BlochSphereRotation(axis=(0.8, -0.3, 1.5), angle=0.9468, phase=2.533))
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
    gate = TwoQubitGate(
        2,
        0,
        gate_semantic=ControlledGateSemantic(
            target_gate=SingleQubitGate(0, BlochSphereRotation(axis=(1, 0, 0), angle=pi, phase=pi / 2))
        ),
    )
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
    gate = TwoQubitGate(
        1,
        2,
        gate_semantic=MatrixGateSemantic(
            [
                [1, 0, 0, 0],
                [0, 0, 1, 0],
                [0, 1, 0, 0],
                [0, 0, 0, 1],
            ],
        ),
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


@pytest.mark.parametrize(
    ("axis", "expected_matrix"),
    [
        ((0, 0, 0), np.eye(4)),
        (
            (1 / 2, 0, 0),
            np.array(
                [
                    [1 / sqrt(2), 0, 0, -1j / sqrt(2)],
                    [0, 1 / sqrt(2), -1j / sqrt(2), 0],
                    [0, -1j / sqrt(2), 1 / sqrt(2), 0],
                    [-1j / sqrt(2), 0, 0, 1 / sqrt(2)],
                ]
            ),
        ),
        ((1 / 2, 1 / 2, 0), np.array([[1, 0, 0, 0], [0, 0, -1j, 0], [0, -1j, 0, 0], [0, 0, 0, 1]])),
        (
            (1 / 2, 1 / 2, 1 / 2),
            np.exp(-1j * np.pi / 4) * np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]]),
        ),
    ],
)
def test_canonical_gate(axis: AxisLike, expected_matrix: NDArray[Any]) -> None:
    gate = TwoQubitGate(0, 1, gate_semantic=CanonicalGateSemantic(axis))

    np.testing.assert_almost_equal(get_matrix(gate, 2), expected_matrix)
