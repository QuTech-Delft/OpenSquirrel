from __future__ import annotations

import math

import pytest

from opensquirrel.decomposer.aba_decomposer import XYXDecomposer
from opensquirrel.decomposer.general_decomposer import check_gate_replacement
from opensquirrel.default_gates import CNOT, CR, H, I, Rx, Ry, S, X, Y
from opensquirrel.ir import BlochSphereRotation, Gate


@pytest.fixture(name="decomposer")
def decomposer_fixture() -> XYXDecomposer:
    return XYXDecomposer()


def test_identity(decomposer: XYXDecomposer) -> None:
    gate = I()(0)
    decomposed_gate = decomposer.decompose(gate)
    assert decomposed_gate == []


@pytest.mark.parametrize(
    ("gate", "expected_result"),
    [
        (CNOT()(0, 1), [CNOT()(0, 1)]),
        (CR(2.123)(2, 3), [CR(2.123)(2, 3)]),
        (S()(0), [Rx(-math.pi / 2)(0), Ry(math.pi / 2)(0), Rx(math.pi / 2)(0)]),
        (Y()(0), [Ry(math.pi)(0)]),
        (Ry(0.9)(0), [Ry(0.9)(0)]),
        (X()(0), [Rx(math.pi)(0)]),
        (Rx(0.123)(0), [Rx(0.123)(0)]),
        (H()(0), [Ry(math.pi / 2)(0), Rx(math.pi)(0)]),
        (
            BlochSphereRotation(qubit=0, angle=5.21, axis=(1, 2, 3), phase=0.324),
            [Rx(-1.140443520488592)(0), Ry(-1.030183660156084)(0), Rx(0.8251439260060653)(0)],
        ),
    ],
    ids=["CNOT", "CR", "S", "Y", "Ry", "X", "Rx", "H", "arbitrary"],
)
def test_xyx_decomposer(decomposer: XYXDecomposer, gate: Gate, expected_result: list[Gate]) -> None:
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)
    assert decomposer.decompose(gate) == expected_result


def test_find_unused_index() -> None:
    xyx_decomp = XYXDecomposer()
    missing_index = xyx_decomp._find_unused_index()

    assert missing_index == 2
