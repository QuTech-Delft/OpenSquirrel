from math import pi
from typing import TYPE_CHECKING

import pytest

from opensquirrel import CNOT, CR, H, I, Rx, Ry, Rz, S, X, Y
from opensquirrel.ir.semantics import BlochSphereRotation
from opensquirrel.passes.decomposer import YZYDecomposer
from opensquirrel.passes.decomposer.general_decomposer import check_gate_replacement

if TYPE_CHECKING:
    from opensquirrel.ir import Gate


@pytest.fixture
def decomposer() -> YZYDecomposer:
    return YZYDecomposer()


def test_identity(decomposer: YZYDecomposer) -> None:
    gate = I(0)
    decomposed_gate = decomposer.decompose(gate)
    assert decomposed_gate == []


@pytest.mark.parametrize(
    ("gate", "expected_result"),
    [
        (CNOT(0, 1), [CNOT(0, 1)]),
        (CR(2, 3, 2.123), [CR(2, 3, 2.123)]),
        (S(0), [Rz(0, pi / 2)]),
        (Y(0), [Ry(0, pi)]),
        (Ry(0, 0.9), [Ry(0, 0.9)]),
        (X(0), [Ry(0, -pi / 2), Rz(0, pi), Ry(0, pi / 2)]),
        (Rx(0, 0.123), [Ry(0, -pi / 2), Rz(0, 0.12300000000000022), Ry(0, pi / 2)]),
        (H(0), [Ry(0, -pi / 4), Rz(0, pi), Ry(0, pi / 4)]),
        (
            BlochSphereRotation(qubit=0, angle=5.21, axis=(1, 2, 3), phase=0.324),
            [Ry(0, -0.6295818450148737), Rz(0, -0.893533136099803), Ry(0, 0.013919263778408464)],
        ),
    ],
    ids=["CNOT", "CR", "S", "Y", "Ry", "X", "Rx", "H", "arbitrary"],
)
def test_yzy_decomposer(decomposer: YZYDecomposer, gate: Gate, expected_result: list[Gate]) -> None:
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)
    assert decomposer.decompose(gate) == expected_result


def test_find_unused_index() -> None:
    yzy_decomp = YZYDecomposer()
    missing_index = yzy_decomp._find_unused_index()

    assert missing_index == 0
