from pyqtgraph.examples.MultiDataPlot import rng
from itertools import product, starmap
from math import pi, sqrt
from typing import Any

import numpy as np
from scipy.linalg import expm
import numpy.testing
import pytest
from numpy.typing import NDArray

from opensquirrel.common import are_matrices_equivalent_up_to_global_phase
from opensquirrel.ir import AxisLike
from opensquirrel.ir.semantics import (
    BlochSphereRotation,
    CanonicalGateSemantic,
    ControlledGateSemantic,
    MatrixGateSemantic,
)
from opensquirrel.ir.single_qubit_gate import SingleQubitGate
from opensquirrel.ir.two_qubit_gate import TwoQubitGate
from opensquirrel.ir.semantics.canonical_gate import CanonicalAxis
from opensquirrel.utils import get_matrix
from opensquirrel.utils.matrix_expander import can1, can2, canonical_decomposition, nearest_kronecker_product


def random_2x2_unitary():    
    rng = np.random.default_rng()
    h = rng.standard_normal((2, 2)) + 1j * rng.standard_normal((2, 2))
    h = (h + h.conj().T) / 2
    return expm(1j * h)


def random_canonical_axis() -> CanonicalAxis:
    rng = np.random.default_rng()
    axis = np.sort(rng.uniform(0, 0.5, 3))[::-1]
    return CanonicalAxis(axis)


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
        gate_semantic=ControlledGateSemantic(target_bsr=BlochSphereRotation(axis=(1, 0, 0), angle=pi, phase=pi / 2)),
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


@pytest.mark.parametrize(
    ("matrix_a", "matrix_b"),
    [
        (np.array([[1, 0], [0, 1]]), np.array([[1, 0], [0, 1]])),
        (np.array([[0, 1], [1, 0]]), np.array([[1, 0], [0, -1]])),
        (np.array([[0, 1j], [-1j, 0]]), np.array([[1, 0], [0, -1]])),
        (np.array([[1, 0], [0, 1j]], dtype=np.complex128), np.array([[1, 0], [0, -1]], dtype=np.complex128)),
        (1 / np.sqrt(2) * np.array([[1, 1], [1, -1]]), 1 / np.sqrt(2) * np.array([[1, 1], [1, -1]])),
    ],
)
def test_nearest_kronecker_product(matrix_a: NDArray[Any], matrix_b: NDArray[Any]) -> None:
    c = np.kron(matrix_a, matrix_b)
    recovered_matrix_a, recovered_matrix_b = nearest_kronecker_product(c)
    np.testing.assert_almost_equal(c, np.kron(recovered_matrix_a, recovered_matrix_b))


@pytest.mark.parametrize(
    ("axis"),
    [
        (0, 0, 0),
        (1 / 2, 0, 0),
        (1 / 2, 1 / 2, 0),
        (1 / 2, 1 / 2, 1 / 2),
        (1 / 4, 0, 0),
        (1 / 4, 1 / 4, 0),
        (3 / 8, 3 / 8, 0),
        (1 / 4, 1 / 4, 1 / 4),
        (1 / 2, 1 / 4, 0),
        (1 / 2, 1 / 4, 1 / 4),
        (1 / 2, 1 / 2, 1 / 4),
        (1 / 2, 1 / 2, 1 / 12),
    ],
)
def test_canonical_decomposition(axis: tuple[float]) -> None:
    x = can2(axis)

    k1, k2, k3, k4, axis_recov = canonical_decomposition(x)

    y = np.kron(k3, k4) @ can2(axis_recov) @ np.kron(k1, k2)
    assert are_matrices_equivalent_up_to_global_phase(x, y)



def test_canonical_decomposition_nontrivial_local_operators() -> None:

    for _ in range(1024):
        axis = random_canonical_axis()
        local1, local2, local3, local4 = (random_2x2_unitary() for _ in range(4))
        x = np.kron(local1, local2) @ can2(axis) @ np.kron(local3, local4)

        k1, k2, k3, k4, axis_recov = canonical_decomposition(x)

        y = np.kron(k3, k4) @ can2(axis_recov) @ np.kron(k1, k2)
        assert are_matrices_equivalent_up_to_global_phase(x, y)
