from __future__ import annotations

from math import pi

import numpy as np
import pytest

from opensquirrel import X90, H, MinusX90, Rn, Rx, Ry, Rz, TDagger, X, Y, Z
from opensquirrel.common import ATOL
from opensquirrel.ir.semantics import BlochSphereRotation, MatrixGateSemantic
from opensquirrel.ir.single_qubit_gate import SingleQubitGate, try_match_replace_with_default_gate
from opensquirrel.utils import can1


@pytest.mark.parametrize(
    ("gate", "default_gate"),
    [
        (SingleQubitGate(0, BlochSphereRotation(axis=(1, 0, 1), angle=pi, phase=pi / 2)), H(0)),
        (SingleQubitGate(0, BlochSphereRotation(axis=(1, 0, 0), angle=pi, phase=pi / 2)), X(0)),
        (SingleQubitGate(0, BlochSphereRotation(axis=(1, 0, 0), angle=pi / 2, phase=pi / 4)), X90(0)),
        (SingleQubitGate(0, BlochSphereRotation(axis=(-1, 0, 0), angle=-pi / 2, phase=-pi / 4)), X90(0)),
        (
            SingleQubitGate(0, BlochSphereRotation(axis=(1, 0, 0), angle=-pi / 2, phase=-pi / 4)),
            MinusX90(0),
        ),
        (
            SingleQubitGate(0, BlochSphereRotation(axis=(-1, 0, 0), angle=pi / 2, phase=pi / 4)),
            MinusX90(0),
        ),
        (
            SingleQubitGate(0, BlochSphereRotation(axis=(0, 0, 1), angle=-pi / 4, phase=-pi / 8)),
            TDagger(0),
        ),
        (SingleQubitGate(0, BlochSphereRotation(axis=(1, 0, 0), angle=pi / 4, phase=0)), Rx(0, pi / 4)),
        (SingleQubitGate(0, BlochSphereRotation(axis=(0, 1, 0), angle=pi / 3, phase=0)), Ry(0, pi / 3)),
        (
            SingleQubitGate(0, BlochSphereRotation(axis=(0, 0, 1), angle=3 * pi / 4, phase=0)),
            Rz(0, 3 * pi / 4),
        ),
        (
            SingleQubitGate(0, BlochSphereRotation(axis=(1, 0, 1), angle=pi, phase=0)),
            Rn(0, 1, 0, 1, pi, 0),
        ),
    ],
    ids=["H", "X", "X90-1", "X90-2", "mX90-1", "mX90-2", "Tdag", "Rx", "Ry", "Rz", "Rn"],
)
def test_default_gate_matching(gate: SingleQubitGate, default_gate: SingleQubitGate) -> None:
    matched_bsr = try_match_replace_with_default_gate(gate)
    assert matched_bsr == default_gate
    assert matched_bsr.name == default_gate.name


class TestSingleQubitGate:
    @pytest.fixture
    def gate(self) -> SingleQubitGate:
        return H(0)

    def test_equality(self, gate: SingleQubitGate) -> None:
        assert gate == gate

    def test_order_of_composition(self) -> None:
        assert X(0) * Y(0) != Y(0) * X(0)
        assert X(0) * Z(0) != Z(0) * X(0)
        assert Y(0) * Z(0) != Z(0) * Y(0)

    @pytest.mark.parametrize("other_gate", [H(1), X(0), "test"])
    def test_non_equality(self, gate: SingleQubitGate, other_gate: SingleQubitGate) -> None:
        assert gate != other_gate

    def test_init_with_bsr(self) -> None:
        bsr = BlochSphereRotation((0, 0, 1), pi / 2, 0)
        gate = SingleQubitGate(0, gate_semantic=bsr)
        assert gate._matrix is None
        assert gate.bsr == bsr

        matrix = gate.matrix
        assert isinstance(matrix, MatrixGateSemantic)
        assert np.allclose(matrix, can1(bsr.axis, bsr.angle, bsr.phase), atol=ATOL)

    def test_init_with_matrix(self) -> None:
        matrix = MatrixGateSemantic((1 / np.sqrt(2)) * np.array([[1, 1], [1, -1]]))
        gate = SingleQubitGate(0, gate_semantic=matrix)
        assert gate.matrix == matrix
        assert gate._bsr is None

        bsr = gate.bsr
        assert isinstance(bsr, BlochSphereRotation)
        assert bsr == H(0).bsr
