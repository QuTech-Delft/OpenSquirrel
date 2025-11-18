from __future__ import annotations

from math import pi, tau

import numpy as np
import pytest
from numpy.typing import ArrayLike, DTypeLike

from opensquirrel import X90, Y90, H, I, MinusX90, MinusY90, S, SDagger, T, TDagger, X, Y, Z
from opensquirrel.common import ATOL
from opensquirrel.ir.semantics import BlochSphereRotation
from opensquirrel.ir.semantics.bsr import bsr_from_matrix


@pytest.mark.parametrize(
    ("matrix", "bsr"),
    [
        (np.array([[1, 0], [0, 1]]), I(0).bsr),
        ((1 / np.sqrt(2)) * np.array([[1, 1], [1, -1]]), H(0).bsr),
        (np.array([[0, 1], [1, 0]]), X(0).bsr),
        ((1 / 2) * np.array([[1 + 1j, 1 - 1j], [1 - 1j, 1 + 1j]]), X90(0).bsr),
        ((1 / 2) * np.array([[1 - 1j, 1 + 1j], [1 + 1j, 1 - 1j]]), MinusX90(0).bsr),
        (np.array([[0, -1j], [1j, 0]]), Y(0).bsr),
        ((1 / 2) * np.array([[1 + 1j, -1 - 1j], [1 + 1j, 1 + 1j]]), Y90(0).bsr),
        ((1 / 2) * np.array([[1 - 1j, 1 - 1j], [-1 + 1j, 1 - 1j]]), MinusY90(0).bsr),
        (np.array([[1, 0], [0, -1]]), Z(0).bsr),
        (np.array([[1, 0], [0, 1j]]), S(0).bsr),
        (np.array([[1, 0], [0, -1j]]), SDagger(0).bsr),
        (np.array([[1, 0], [0, np.exp(1j * pi / 4)]]), T(0).bsr),
        (np.array([[1, 0], [0, np.exp(-1j * pi / 4)]]), TDagger(0).bsr),
    ],
    ids=["I", "H", "X", "X90", "mX90", "Y", "Y90", "mY90", "Z", "S", "SDagger", "T", "TDagger"],
)
def test_bsr_from_matrix(matrix: ArrayLike | list[list[int | DTypeLike]], bsr: BlochSphereRotation) -> None:
    assert bsr_from_matrix(matrix) == bsr


class TestBlochSphereRotation:
    @pytest.fixture
    def bsr(self) -> BlochSphereRotation:
        return BlochSphereRotation(axis=(1, 0, 0), angle=pi, phase=tau)

    @pytest.mark.parametrize(
        "other_bsr",
        [
            BlochSphereRotation(axis=(1, 0, 0), angle=pi, phase=tau),
            BlochSphereRotation(axis=(1 + ATOL / 2, 0, 0), angle=pi, phase=tau),
            BlochSphereRotation(axis=(1, 0, 0), angle=pi + ATOL / 2, phase=tau),
            BlochSphereRotation(axis=(1, 0, 0), angle=pi, phase=tau + ATOL / 2),
            BlochSphereRotation(axis=(1, 0, 0), angle=pi + tau, phase=tau),
        ],
        ids=["all_equal", "close_axis", "close_angle", "close_phase", "angle+tau"],
    )
    def test_equality(self, bsr: BlochSphereRotation, other_bsr: BlochSphereRotation) -> None:
        assert bsr == other_bsr

    @pytest.mark.parametrize(
        "other_bsr",
        [
            BlochSphereRotation(axis=(0, 1, 0), angle=pi, phase=tau),
            BlochSphereRotation(axis=(1, 0, 0), angle=0, phase=tau),
            BlochSphereRotation(axis=(1, 0, 0), angle=pi, phase=1),
            "test",
        ],
        ids=["axis", "angle", "phase", "type"],
    )
    def test_inequality(self, bsr: BlochSphereRotation, other_bsr: BlochSphereRotation | str) -> None:
        assert bsr != other_bsr

    def test_is_identity(self, bsr: BlochSphereRotation) -> None:
        assert I(42).is_identity()
        assert not bsr.is_identity()
