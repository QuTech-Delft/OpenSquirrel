from __future__ import annotations

from math import pi

import pytest

from opensquirrel import CNOT, CR, H, I, Rx, Ry, S, X, Y
from opensquirrel.ir.semantics import BlochSphereRotation
from opensquirrel.ir.single_qubit_gate import SingleQubitGate
from opensquirrel.passes.decomposer import YXYDecomposer
from opensquirrel.passes.decomposer.general_decomposer import check_gate_replacement


@pytest.fixture
def decomposer() -> YXYDecomposer:
    return YXYDecomposer()


def test_identity(decomposer: YXYDecomposer) -> None:
    gate = I(0)
    decomposed_gate = decomposer.decompose(gate)
    assert decomposed_gate == []


@pytest.mark.parametrize(
    ("gate", "expected_result"),
    [
        (CNOT(0, 1), [CNOT(0, 1)]),
        (CR(2, 3, 2.123), [CR(2, 3, 2.123)]),
        (S(0), [Ry(0, pi / 2), Rx(0, pi / 2), Ry(0, -pi / 2)]),
        (Y(0), [Ry(0, pi)]),
        (Ry(0, 0.9), [Ry(0, 0.9)]),
        (X(0), [Rx(0, pi)]),
        (Rx(0, 0.123), [Rx(0, 0.123)]),
        (H(0), [Ry(0, pi / 4), Rx(0, pi), Ry(0, -pi / 4)]),
        (
            SingleQubitGate(qubit=0, gate_semantic=BlochSphereRotation(angle=5.21, axis=(1, 2, 3), phase=0.324)),
            [Ry(0, 0.9412144817800217), Rx(0, -0.893533136099803), Ry(0, -1.5568770630164868)],
        ),
    ],
    ids=["CNOT", "CR", "S", "Y", "Ry", "X", "Rx", "H", "arbitrary"],
)
def test_yxy_decomposer(
    decomposer: YXYDecomposer, gate: SingleQubitGate, expected_result: list[SingleQubitGate]
) -> None:
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)
    assert decomposer.decompose(gate) == expected_result


def test_find_unused_index() -> None:
    yxy_decomp = YXYDecomposer()
    missing_index = yxy_decomp._find_unused_index()

    assert missing_index == 2
