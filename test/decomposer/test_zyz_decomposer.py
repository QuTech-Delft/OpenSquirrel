from __future__ import annotations

import math

import pytest

from opensquirrel.decomposer.aba_decomposer import ZYZDecomposer
from opensquirrel.decomposer.general_decomposer import check_gate_replacement
from opensquirrel.default_gates import CNOT, CR, H, I, Rx, Ry, Rz, S, Sdag, X, Y, Z
from opensquirrel.ir import BlochSphereRotation, Gate


@pytest.fixture(name="decomposer")
def decomposer_fixture() -> ZYZDecomposer:
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
        (X(0), [S(0), Ry(0, math.pi), Sdag(0)]),
        (Rx(0, 0.9), [S(0), Ry(0, 0.9), Sdag(0)]),
        (Y(0), [Ry(0, math.pi)]),
        (Ry(0, 0.9), [Ry(0, 0.9)]),
        (Z(0), [Rz(0, math.pi)]),
        (Rz(0, 0.123), [Rz(0, 0.123)]),
        (H(0), [Rz(0, math.pi), Ry(0, math.pi / 2)]),
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
