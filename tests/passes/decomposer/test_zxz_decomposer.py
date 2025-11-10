from __future__ import annotations

from math import pi
from typing import TYPE_CHECKING

import pytest

from opensquirrel import CNOT, CR, H, I, Rx, Ry, Rz, X, Y, Z
from opensquirrel.ir.semantics import BlochSphereRotation
from opensquirrel.passes.decomposer import ZXZDecomposer
from opensquirrel.passes.decomposer.general_decomposer import check_gate_replacement
from opensquirrel.ir.single_qubit_gate import SingleQubitGate

if TYPE_CHECKING:
    from opensquirrel.ir import Gate


@pytest.fixture
def decomposer() -> ZXZDecomposer:
    return ZXZDecomposer()


def test_identity(decomposer: ZXZDecomposer) -> None:
    gate = I(0)
    decomposed_gate = decomposer.decompose(gate)
    assert decomposed_gate == []


@pytest.mark.parametrize(
    ("gate", "expected_result"),
    [
        (CNOT(0, 1), [CNOT(0, 1)]),
        (CR(2, 3, 2.123), [CR(2, 3, 2.123)]),
        (X(0), [Rx(0, pi)]),
        (Rx(0, 0.9), [Rx(0, 0.9)]),
        (Y(0), [Rz(0, -pi / 2), Rx(0, pi), Rz(0, pi / 2)]),
        (Ry(0, 0.9), [Rz(0, -pi / 2), Rx(0, 0.9000000000000004), Rz(0, pi / 2)]),
        (Z(0), [Rz(0, pi)]),
        (Rz(0, 0.123), [Rz(0, 0.123)]),
        (H(0), [Rz(0, pi / 2), Rx(0, pi / 2), Rz(0, pi / 2)]),
        (
            SingleQubitGate.from_bsr(qubit=0, bsr=BlochSphereRotation(angle=5.21, axis=(1, 2, 3), phase=0.324)),
            [Rz(0, -1.5521517485841891), Rx(0, -0.6209410696845807), Rz(0, 0.662145687003993)],
        ),
    ],
    ids=["CNOT", "CR", "X", "Rx", "Y", "Ry", "Z", "Rz", "H", "arbitrary"],
)
def test_zxz_decomposer(decomposer: ZXZDecomposer, gate: SingleQubitGate, expected_result: list[Gate]) -> None:
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)
    assert decomposer.decompose(gate) == expected_result


@pytest.mark.parametrize(
    "gate",
    [
        Ry(0, -pi / 2),
        SingleQubitGate.from_bsr(qubit=0, bsr=BlochSphereRotation(axis=[0.0, 1.0, 0.0], angle=-pi / 2, phase=0.0)),
        SingleQubitGate.from_bsr(qubit=0, bsr=BlochSphereRotation(axis=[0.0, -1.0, 0.0], angle=pi / 2, phase=0.0)),
    ],
    ids=["Ry(-pi/2)", "BSR_1 of Ry(-pi/2)", "BSR_2 of Ry(-pi/2)"],
)
def test_specific_gate(decomposer: ZXZDecomposer, gate: SingleQubitGate) -> None:
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)


def test_find_unused_index() -> None:
    zxz_decomp = ZXZDecomposer()
    missing_index = zxz_decomp._find_unused_index()

    assert missing_index == 1
