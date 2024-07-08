from __future__ import annotations

import math

import pytest

from opensquirrel.decomposer.aba_decomposer import XYXDecomposer
from opensquirrel.default_gates import CNOT, CR, H, I, Rx, Ry, S, X, Y
from opensquirrel.ir import BlochSphereRotation, Float, Gate, Qubit


@pytest.fixture(name="decomposer")
def decomposer_fixture() -> XYXDecomposer:
    return XYXDecomposer()


@pytest.mark.parametrize(
    "gate, expected_result",
    [
        (CNOT(Qubit(0), Qubit(1)), [CNOT(Qubit(0), Qubit(1))]),
        (CR(Qubit(2), Qubit(3), Float(2.123)), [CR(Qubit(2), Qubit(3), Float(2.123))]),
        (I(Qubit(0)), []),
        (
            S(Qubit(0)),
            [Rx(Qubit(0), Float(-math.pi / 2)), Ry(Qubit(0), Float(math.pi / 2)), Rx(Qubit(0), Float(math.pi / 2))],
        ),
        (Y(Qubit(0)), [Ry(Qubit(0), Float(math.pi))]),
        (Ry(Qubit(0), Float(0.9)), [Ry(Qubit(0), Float(0.9))]),
        (X(Qubit(0)), [Rx(Qubit(0), Float(math.pi))]),
        (Rx(Qubit(0), Float(0.123)), [Rx(Qubit(0), Float(0.123))]),
        (H(Qubit(0)), [Ry(Qubit(0), Float(math.pi / 2)), Rx(Qubit(0), Float(math.pi))]),
        (
            BlochSphereRotation(qubit=Qubit(0), angle=5.21, axis=(1, 2, 3), phase=0.324),
            [
                Rx(Qubit(0), Float(-1.140443520488592)),
                Ry(Qubit(0), Float(-1.030183660156084)),
                Rx(Qubit(0), Float(0.8251439260060653)),
            ],
        ),
    ],
    ids=["CNOT", "CR", "I", "S", "Y", "Ry", "X", "Rx", "H", "arbitrary"],
)
def test_xyx_decomposer(decomposer: XYXDecomposer, gate: Gate, expected_result: list[Gate]) -> None:
    assert decomposer.decompose(gate) == expected_result
