from __future__ import annotations

import math

import pytest

from opensquirrel.default_gates import CNOT, CR, H, I, Rx, Rz, S, X, Z
from opensquirrel.ir import BlochSphereRotation, Float, Gate
from opensquirrel.passes.decomposer.aba_decomposer import XZXDecomposer
from opensquirrel.passes.decomposer.general_decomposer import check_gate_replacement


@pytest.fixture(name="decomposer")
def decomposer_fixture() -> XZXDecomposer:
    return XZXDecomposer()


def test_identity(decomposer: XZXDecomposer) -> None:
    gate = I(0)
    decomposed_gate = decomposer.decompose(gate)
    assert decomposed_gate == []


@pytest.mark.parametrize(
    ("gate", "expected_result"),
    [
        (CNOT(0, 1), [CNOT(0, 1)]),
        (CR(2, 3, Float(2.123)), [CR(2, 3, Float(2.123))]),
        (S(0), [Rz(0, Float(math.pi / 2))]),
        (Z(0), [Rz(0, Float(math.pi))]),
        (Rz(0, Float(0.9)), [Rz(0, Float(0.9))]),
        (X(0), [Rx(0, Float(math.pi))]),
        (Rx(0, Float(0.123)), [Rx(0, Float(0.123))]),
        (
            H(0),
            [
                Rx(0, Float(math.pi / 2)),
                Rz(0, Float(math.pi / 2)),
                Rx(0, Float(math.pi / 2)),
            ],
        ),
        (
            BlochSphereRotation(qubit=0, angle=5.21, axis=(1, 2, 3), phase=0.324),
            [
                Rx(0, Float(0.43035280630630446)),
                Rz(0, Float(-1.030183660156084)),
                Rx(0, Float(-0.7456524007888308)),
            ],
        ),
    ],
    ids=["CNOT", "CR", "S", "Y", "Ry", "X", "Rx", "H", "arbitrary"],
)
def test_xzx_decomposer(decomposer: XZXDecomposer, gate: Gate, expected_result: list[Gate]) -> None:
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)
    assert decomposer.decompose(gate) == expected_result


def test_find_unused_index() -> None:
    xzx_decomp = XZXDecomposer()
    missing_index = xzx_decomp._find_unused_index()

    assert missing_index == 1
