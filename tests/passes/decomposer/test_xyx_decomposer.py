from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pytest

from opensquirrel import CNOT, CR, H, I, Rx, Ry, S, X, Y
from opensquirrel.ir.semantics import BlochSphereRotation
from opensquirrel.passes.decomposer import XYXDecomposer
from opensquirrel.passes.decomposer.general_decomposer import check_gate_replacement

if TYPE_CHECKING:
    from opensquirrel.ir import Gate


@pytest.fixture
def decomposer() -> XYXDecomposer:
    return XYXDecomposer()


def test_identity(decomposer: XYXDecomposer) -> None:
    gate = I(0)
    decomposed_gate = decomposer.decompose(gate)
    assert decomposed_gate == []


@pytest.mark.parametrize(
    ("gate", "expected_result"),
    [
        (CNOT(0, 1), [CNOT(0, 1)]),
        (CR(2, 3, 2.123), [CR(2, 3, 2.123)]),
        (S(0), [Rx(0, -math.pi / 2), Ry(0, math.pi / 2), Rx(0, math.pi / 2)]),
        (Y(0), [Ry(0, math.pi)]),
        (Ry(0, 0.9), [Ry(0, 0.9)]),
        (X(0), [Rx(0, math.pi)]),
        (Rx(0, 0.123), [Rx(0, 0.123)]),
        (H(0), [Ry(0, math.pi / 2), Rx(0, math.pi)]),
        (
            BlochSphereRotation(qubit=0, angle=5.21, axis=(1, 2, 3), phase=0.324),
            [Rx(0, -1.140443520488592), Ry(0, -1.030183660156084), Rx(0, 0.8251439260060653)],
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
