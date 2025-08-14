from __future__ import annotations

from math import pi
from typing import TYPE_CHECKING

import pytest

from opensquirrel import CNOT, CR, H, I, Rx, Ry, Rz, X, Y, Z
from opensquirrel.ir.semantics import BlochSphereRotation
from opensquirrel.passes.decomposer import ZYZDecomposer
from opensquirrel.passes.decomposer.general_decomposer import check_gate_replacement

if TYPE_CHECKING:
    from opensquirrel.ir import Gate


@pytest.fixture
def decomposer() -> ZYZDecomposer:
    return ZYZDecomposer()


def test_identity(decomposer: ZYZDecomposer) -> None:
    gate = I(0)
    decomposed_gate = decomposer.decompose(gate)
    assert decomposed_gate == []


@pytest.mark.parametrize(
    ("gate", "expected_result"),
    [
        (CNOT(0, 1), [CNOT(0, 1)]),
        (CR(2, 3, 2.123), [CR(2, 3, 2.123)]),
        (X(0), [Rz(0, pi / 2), Ry(0, pi), Rz(0, -pi / 2)]),
        (Rx(0, 0.9), [Rz(0, pi / 2), Ry(0, 0.9), Rz(0, -pi / 2)]),
        (Y(0), [Ry(0, pi)]),
        (Ry(0, 0.9), [Ry(0, 0.9)]),
        (Z(0), [Rz(0, pi)]),
        (Rz(0, 0.123), [Rz(0, 0.123)]),
        (H(0), [Rz(0, pi), Ry(0, pi / 2)]),
        (
            BlochSphereRotation(qubit=0, angle=5.21, axis=(1, 2, 3), phase=0.324),
            [Rz(0, 0.018644578210710527), Ry(0, -0.6209410696845807), Rz(0, -0.9086506397909061)],
        ),
    ],
    ids=["CNOT", "CR", "X", "Rx", "Y", "Ry", "Z", "Rz", "H", "arbitrary"],
)
def test_zyz_decomposer(decomposer: ZYZDecomposer, gate: Gate, expected_result: list[Gate]) -> None:
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)
    assert decomposer.decompose(gate) == expected_result


def test_find_unused_index() -> None:
    zyz_decomp = ZYZDecomposer()
    missing_index = zyz_decomp._find_unused_index()

    assert missing_index == 0
