from __future__ import annotations

import math

import pytest

from opensquirrel.decomposer.aba_decomposer import YZYDecomposer
from opensquirrel.decomposer.general_decomposer import check_gate_replacement
from opensquirrel.default_gates import CNOT, CR, H, I, Rx, Ry, Rz, S, X, Y
from opensquirrel.ir import BlochSphereRotation, Gate


@pytest.fixture(name="decomposer")
def decomposer_fixture() -> YZYDecomposer:
    return YZYDecomposer()


def test_identity(decomposer: YZYDecomposer) -> None:
    gate = I()(0)
    decomposed_gate = decomposer.decompose(gate)
    assert decomposed_gate == []


@pytest.mark.parametrize(
    ("gate", "expected_result"),
    [
        (CNOT()(0, 1), [CNOT()(0, 1)]),
        (CR(2.123)(2, 3), [CR(2.123)(2, 3)]),
        (S()(0), [Rz(math.pi / 2)(0)]),
        (Y()(0), [Ry(math.pi)(0)]),
        (Ry(0.9)(0), [Ry(0.9)(0)]),
        (X()(0), [Ry(-math.pi / 2)(0), Rz(math.pi)(0), Ry(math.pi / 2)(0)]),
        (
            Rx(0.123)(0),
            [Ry(-math.pi / 2)(0), Rz(0.12300000000000022)(0), Ry(math.pi / 2)(0)],
        ),
        (H()(0), [Ry(-math.pi / 4)(0), Rz(math.pi)(0), Ry(math.pi / 4)(0)]),
        (
            BlochSphereRotation(qubit=0, angle=5.21, axis=(1, 2, 3), phase=0.324),
            [Ry(-0.6295818450148737)(0), Rz(-0.893533136099803)(0), Ry(0.013919263778408464)(0)],
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
