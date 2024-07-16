from __future__ import annotations

import math

import pytest

from opensquirrel.decomposer.aba_decomposer import YXYDecomposer
from opensquirrel.decomposer.general_decomposer import check_gate_replacement
from opensquirrel.default_gates import CNOT, CR, H, I, Rx, Ry, S, X, Y
from opensquirrel.ir import BlochSphereRotation, Float, Gate, Qubit


@pytest.fixture(name="decomposer")
def decomposer_fixture() -> YXYDecomposer:
    return YXYDecomposer()


def test_identity(decomposer: YXYDecomposer) -> None:
    gate = I(Qubit(0))
    decomposed_gate = decomposer.decompose(gate)
    assert decomposed_gate == []


@pytest.mark.parametrize(
    "gate, expected_result",
    [
        (CNOT(Qubit(0), Qubit(1)), [CNOT(Qubit(0), Qubit(1))]),
        (CR(Qubit(2), Qubit(3), Float(2.123)), [CR(Qubit(2), Qubit(3), Float(2.123))]),
        (
            S(Qubit(0)),
            [Ry(Qubit(0), Float(math.pi / 2)), Rx(Qubit(0), Float(math.pi / 2)), Ry(Qubit(0), Float(-math.pi / 2))],
        ),
        (Y(Qubit(0)), [Ry(Qubit(0), Float(math.pi))]),
        (Ry(Qubit(0), Float(0.9)), [Ry(Qubit(0), Float(0.9))]),
        (X(Qubit(0)), [Rx(Qubit(0), Float(math.pi))]),
        (Rx(Qubit(0), Float(0.123)), [Rx(Qubit(0), Float(0.123))]),
        (
            H(Qubit(0)),
            [
                Ry(Qubit(0), Float(math.pi / 4)),
                Rx(Qubit(0), Float(math.pi)),
                Ry(Qubit(0), Float(-math.pi / 4)),
            ],
        ),
        (
            BlochSphereRotation(qubit=Qubit(0), angle=5.21, axis=(1, 2, 3), phase=0.324),
            [
                Ry(Qubit(0), Float(0.9412144817800217)),
                Rx(Qubit(0), Float(-0.893533136099803)),
                Ry(Qubit(0), Float(-1.5568770630164868)),
            ],
        ),
    ],
    ids=["CNOT", "CR", "S", "Y", "Ry", "X", "Rx", "H", "arbitrary"],
)
def test_yxy_decomposer(decomposer: YXYDecomposer, gate: Gate, expected_result: list[Gate]) -> None:
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)
    assert decomposer.decompose(gate) == expected_result
