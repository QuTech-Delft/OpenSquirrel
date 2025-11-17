from __future__ import annotations

from math import pi, tau

import pytest

from opensquirrel import I
from opensquirrel.common import ATOL
from opensquirrel.ir.semantics import BlochSphereRotation


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
