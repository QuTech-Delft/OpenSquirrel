from __future__ import annotations

import math

import pytest

from opensquirrel.decomposer.aba_decomposer import ZYZDecomposer
from opensquirrel.default_gates import CNOT, CR, H, I, Rx, Ry, Rz, S, Sdag, X, Y, Z
from opensquirrel.ir import BlochSphereRotation, Float, Gate, Qubit


@pytest.fixture(name="decomposer")
def decomposer_fixture() -> ZYZDecomposer:
    return ZYZDecomposer()


@pytest.mark.parametrize(
    "gate, expected_result",
    [
        (CNOT(Qubit(0), Qubit(1)), [CNOT(Qubit(0), Qubit(1))]),
        (CR(Qubit(2), Qubit(3), Float(2.123)), [CR(Qubit(2), Qubit(3), Float(2.123))]),
        (I(Qubit(0)), []),
        (X(Qubit(0)), [S(Qubit(0)), Ry(Qubit(0), Float(math.pi)), Sdag(Qubit(0))]),
        (Rx(Qubit(0), Float(0.9)), [S(Qubit(0)), Ry(Qubit(0), Float(0.9)), Sdag(Qubit(0))]),
        (Y(Qubit(0)), [Ry(Qubit(0), Float(math.pi))]),
        (Ry(Qubit(0), Float(0.9)), [Ry(Qubit(0), Float(0.9))]),
        (Z(Qubit(0)), [Rz(Qubit(0), Float(math.pi))]),
        (Rz(Qubit(0), Float(0.123)), [Rz(Qubit(0), Float(0.123))]),
        (H(Qubit(0)), [Rz(Qubit(0), Float(math.pi)), Ry(Qubit(0), Float(math.pi / 2))]),
        (
            BlochSphereRotation(qubit=Qubit(0), angle=5.21, axis=(1, 2, 3), phase=0.324),
            [
                Rz(Qubit(0), Float(0.018644578210710527)),
                Ry(Qubit(0), Float(-0.6209410696845807)),
                Rz(Qubit(0), Float(-0.9086506397909061)),
            ],
        ),
    ],
    ids=["CNOT", "CR", "I", "X", "Rx", "Y", "Ry", "Z", "Rz", "H", "arbitrary"],
)
def test_zyz_decomposer(decomposer: ZYZDecomposer, gate: Gate, expected_result: list[Gate]) -> None:
    assert decomposer.decompose(gate) == expected_result
