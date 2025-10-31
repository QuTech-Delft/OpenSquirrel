from __future__ import annotations

from math import pi, tau

import pytest

from opensquirrel import X90, Y90, Z90, H, I, MinusX90, Rn, Rx, Ry, Rz, TDagger, U, X
from opensquirrel.common import ATOL
from opensquirrel.ir import Qubit
from opensquirrel.ir.semantics import BlochSphereRotation


def assert_equal_upto_phase(gate1: BlochSphereRotation, gate2: BlochSphereRotation) -> None:
    assert gate1.qubit == gate2.qubit
    assert gate1.axis == gate2.axis
    assert gate1.angle == gate2.angle


class TestBlochSphereRotation:
    @pytest.fixture
    def gate(self) -> BlochSphereRotation:
        return BlochSphereRotation(qubit=42, axis=(1, 0, 0), angle=pi, phase=tau)

    @pytest.mark.parametrize(
        "other_gate",
        [
            BlochSphereRotation(qubit=42, axis=(1, 0, 0), angle=pi, phase=tau),
            BlochSphereRotation(qubit=42, axis=(1 + ATOL / 2, 0, 0), angle=pi, phase=tau),
            BlochSphereRotation(qubit=42, axis=(1, 0, 0), angle=pi + ATOL / 2, phase=tau),
            BlochSphereRotation(qubit=42, axis=(1, 0, 0), angle=pi, phase=tau + ATOL / 2),
            BlochSphereRotation(qubit=42, axis=(1, 0, 0), angle=pi + tau, phase=tau),
        ],
        ids=["all_equal", "close_axis", "close_angle", "close_phase", "angle+tau"],
    )
    def test_equality(self, gate: BlochSphereRotation, other_gate: BlochSphereRotation) -> None:
        assert gate == other_gate

    @pytest.mark.parametrize(
        "other_gate",
        [
            BlochSphereRotation(qubit=43, axis=(1, 0, 0), angle=pi, phase=tau),
            BlochSphereRotation(qubit=42, axis=(0, 1, 0), angle=pi, phase=tau),
            BlochSphereRotation(qubit=42, axis=(1, 0, 0), angle=0, phase=tau),
            BlochSphereRotation(qubit=42, axis=(1, 0, 0), angle=pi, phase=1),
            "test",
        ],
        ids=["qubit", "axis", "angle", "phase", "type"],
    )
    def test_inequality(self, gate: BlochSphereRotation, other_gate: BlochSphereRotation | str) -> None:
        assert gate != other_gate

    def test_get_qubit_operands(self, gate: BlochSphereRotation) -> None:
        assert gate.get_qubit_operands() == [Qubit(42)]

    def test_is_identity(self, gate: BlochSphereRotation) -> None:
        assert I(42).is_identity()
        assert not gate.is_identity()

    def test_u_gate(self) -> None:
        assert U(0, 0, 0, 0).is_identity()
        u = U(0, pi / 2, 0, 0)
        assert_equal_upto_phase(u, Y90(0))
        u = U(0, 0, pi / 2, 0)
        assert_equal_upto_phase(u, Z90(0))

    @pytest.mark.parametrize(
        ("bsr", "default_gate"),
        [
            (BlochSphereRotation(qubit=0, axis=(1, 0, 1), angle=pi, phase=pi / 2), H(0)),
            (BlochSphereRotation(qubit=0, axis=(1, 0, 0), angle=pi, phase=pi / 2), X(0)),
            (BlochSphereRotation(qubit=0, axis=(1, 0, 0), angle=pi / 2, phase=pi / 4), X90(0)),
            (BlochSphereRotation(qubit=0, axis=(-1, 0, 0), angle=-pi / 2, phase=-pi / 4), X90(0)),
            (BlochSphereRotation(qubit=0, axis=(1, 0, 0), angle=-pi / 2, phase=-pi / 4), MinusX90(0)),
            (BlochSphereRotation(qubit=0, axis=(-1, 0, 0), angle=pi / 2, phase=pi / 4), MinusX90(0)),
            (BlochSphereRotation(qubit=0, axis=(0, 0, 1), angle=-pi / 4, phase=-pi / 8), TDagger(0)),
            (BlochSphereRotation(qubit=0, axis=(1, 0, 0), angle=pi / 4, phase=0), Rx(0, pi / 4)),
            (BlochSphereRotation(qubit=0, axis=(0, 1, 0), angle=pi / 3, phase=0), Ry(0, pi / 3)),
            (BlochSphereRotation(qubit=0, axis=(0, 0, 1), angle=3 * pi / 4, phase=0), Rz(0, 3 * pi / 4)),
            (BlochSphereRotation(qubit=0, axis=(1, 0, 1), angle=pi, phase=0), Rn(0, 1, 0, 1, pi, 0)),
        ],
        ids=["H", "X", "X90-1", "X90-2", "mX90-1", "mX90-2", "Tdag", "Rx", "Ry", "Rz", "Rn"],
    )
    def test_default_gate_matching(self, bsr: BlochSphereRotation, default_gate: BlochSphereRotation) -> None:
        matched_bsr = BlochSphereRotation.try_match_replace_with_default(bsr)
        assert matched_bsr == default_gate
        assert matched_bsr.name == default_gate.name
