from __future__ import annotations

import math

import pytest

from opensquirrel.decomposer.aba_decomposer import ZXZDecomposer
from opensquirrel.decomposer.general_decomposer import check_gate_replacement
from opensquirrel.default_gates import CNOT, CR, H, I, Rx, Ry, Rz, X, Y, Z
from opensquirrel.ir import BlochSphereRotation, Gate


@pytest.fixture(name="decomposer")
def decomposer_fixture() -> ZXZDecomposer:
    return ZXZDecomposer()


def test_identity(decomposer: ZXZDecomposer) -> None:
    gate = I()(0)
    decomposed_gate = decomposer.decompose(gate)
    assert decomposed_gate == []


@pytest.mark.parametrize(
    ("gate", "expected_result"),
    [
        (CNOT()(0, 1), [CNOT()(0, 1)]),
        (CR(2.123)(2, 3), [CR(2.123)(2, 3)]),
        (X()(0), [Rx(math.pi)(0)]),
        (Rx(0.9)(0), [Rx(0.9)(0)]),
        (Y()(0), [Rz(-math.pi / 2)(0), Rx(math.pi)(0), Rz(math.pi / 2)(0)]),
        (Ry(0.9)(0), [Rz(-math.pi / 2)(0), Rx(0.9000000000000004)(0), Rz(math.pi / 2)(0)]),
        (Z()(0), [Rz(math.pi)(0)]),
        (Rz(0.123)(0), [Rz(0.123)(0)]),
        (H()(0), [Rz(math.pi / 2)(0), Rx(math.pi / 2)(0), Rz(math.pi / 2)(0)]),
        (
            BlochSphereRotation(qubit=0, angle=5.21, axis=(1, 2, 3), phase=0.324),
            [Rz(-1.5521517485841891)(0), Rx(-0.6209410696845807)(0), Rz(0.662145687003993)(0)],
        ),
    ],
    ids=["CNOT", "CR", "X", "Rx", "Y", "Ry", "Z", "Rz", "H", "arbitrary"],
)
def test_zxz_decomposer(decomposer: ZXZDecomposer, gate: Gate, expected_result: list[Gate]) -> None:
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)
    assert decomposer.decompose(gate) == expected_result


def test_find_unused_index() -> None:
    zxz_decomp = ZXZDecomposer()
    missing_index = zxz_decomp._find_unused_index()

    assert missing_index == 1
