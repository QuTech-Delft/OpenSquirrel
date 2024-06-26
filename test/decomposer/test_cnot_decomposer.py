from __future__ import annotations

import math

import pytest

from opensquirrel.decomposer.cnot_decomposer import CNOTDecomposer
from opensquirrel.default_gates import CNOT, CZ, SWAP, H, Ry, Rz, X
from opensquirrel.ir import ControlledGate, Float, Gate, Qubit


@pytest.fixture(name="decomposer")
def decomposer_fixture() -> CNOTDecomposer:
    return CNOTDecomposer()


@pytest.mark.parametrize(
    "gate,expected_result", [(H(Qubit(0)), [H(Qubit(0))]), (Rz(Qubit(0), Float(2.345)), [Rz(Qubit(0), Float(2.345))])]
)
def test_ignores_1q_gates(decomposer: CNOTDecomposer, gate: Gate, expected_result: list[Gate]) -> None:
    assert decomposer.decompose(gate) == expected_result


def test_ignores_matrix_gate(decomposer: CNOTDecomposer) -> None:
    assert decomposer.decompose(SWAP(Qubit(4), Qubit(3))) == [SWAP(Qubit(4), Qubit(3))]


def test_ignores_double_controlled(decomposer: CNOTDecomposer) -> None:
    g = ControlledGate(
        control_qubit=Qubit(5), target_gate=ControlledGate(control_qubit=Qubit(2), target_gate=X(Qubit(0)))
    )
    assert decomposer.decompose(g) == [g]


def test_CNOT(decomposer: CNOTDecomposer) -> None:
    assert decomposer.decompose(CNOT(Qubit(0), Qubit(1))) == [CNOT(Qubit(0), Qubit(1))]


def test_CZ(decomposer: CNOTDecomposer) -> None:
    assert decomposer.decompose(CZ(Qubit(0), Qubit(1))) == [
        Rz(Qubit(1), Float(math.pi)),
        Ry(Qubit(1), Float(math.pi / 2)),
        CNOT(Qubit(0), Qubit(1)),
        Ry(Qubit(1), Float(-math.pi / 2)),
        Rz(Qubit(1), Float(math.pi)),
    ]
