from __future__ import annotations

import math

import pytest

from opensquirrel.decomposer.aba_decomposer import ZXZDecomposer
from opensquirrel.decomposer.general_decomposer import check_gate_replacement
from opensquirrel.default_gates import CNOT, CR, H, I, Rx, Ry, Rz, X, Y, Z
from opensquirrel.ir import BlochSphereRotation, Float, Gate, Qubit


@pytest.fixture(name="decomposer")
def decomposer_fixture() -> ZXZDecomposer:
    return ZXZDecomposer()


def test_identity(decomposer: ZXZDecomposer) -> None:
    gate = I(Qubit(0))
    decomposed_gate = decomposer.decompose(gate)
    assert decomposed_gate == []


@pytest.mark.parametrize(
    "gate, expected_result",
    [
        (CNOT(Qubit(0), Qubit(1)), [CNOT(Qubit(0), Qubit(1))]),
        (CR(Qubit(2), Qubit(3), Float(2.123)), [CR(Qubit(2), Qubit(3), Float(2.123))]),
        (X(Qubit(0)), [Rx(Qubit(0), Float(math.pi))]),
        (Rx(Qubit(0), Float(0.9)), [Rx(Qubit(0), Float(0.9))]),
        (
            Y(Qubit(0)),
            [Rz(Qubit(0), Float(-math.pi / 2)), Rx(Qubit(0), Float(math.pi)), Rz(Qubit(0), Float(math.pi / 2))],
        ),
        (
            Ry(Qubit(0), Float(0.9)),
            [
                Rz(Qubit(0), Float(-math.pi / 2)),
                Rx(Qubit(0), Float(0.9000000000000004)),
                Rz(Qubit(0), Float(math.pi / 2)),
            ],
        ),
        (Z(Qubit(0)), [Rz(Qubit(0), Float(math.pi))]),
        (Rz(Qubit(0), Float(0.123)), [Rz(Qubit(0), Float(0.123))]),
        (
            H(Qubit(0)),
            [Rz(Qubit(0), Float(math.pi / 2)), Rx(Qubit(0), Float(math.pi / 2)), Rz(Qubit(0), Float(math.pi / 2))],
        ),
        (
            BlochSphereRotation(qubit=Qubit(0), angle=5.21, axis=(1, 2, 3), phase=0.324),
            [
                Rz(Qubit(0), Float(-1.5521517485841891)),
                Rx(Qubit(0), Float(-0.6209410696845807)),
                Rz(Qubit(0), Float(0.662145687003993)),
            ],
        ),
    ],
    ids=["CNOT", "CR", "X", "Rx", "Y", "Ry", "Z", "Rz", "H", "arbitrary"],
)
def test_zxz_decomposer(decomposer: ZXZDecomposer, gate: Gate, expected_result: list[Gate]) -> None:
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)
    assert decomposer.decompose(gate) == expected_result
