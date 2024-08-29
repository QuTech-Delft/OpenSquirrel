from __future__ import annotations

import math

import pytest

from opensquirrel.decomposer.cnot_decomposer import CNOTDecomposer
from opensquirrel.decomposer.general_decomposer import check_gate_replacement
from opensquirrel.default_gates import CNOT, CZ, SWAP, H, Ry, Rz, X
from opensquirrel.ir import ControlledGate, Float, Gate, Qubit


@pytest.fixture(name="decomposer")
def decomposer_fixture() -> CNOTDecomposer:
    return CNOTDecomposer()


@pytest.mark.parametrize(
    ("gate", "expected_result"),
    [(H(Qubit(0)), [H(Qubit(0))]), (Rz(Qubit(0), Float(2.345)), [Rz(Qubit(0), Float(2.345))])],
)
def test_ignores_1q_gates(decomposer: CNOTDecomposer, gate: Gate, expected_result: list[Gate]) -> None:
    check_gate_replacement(gate, expected_result)
    assert decomposer.decompose(gate) == expected_result


def test_ignores_matrix_gate(decomposer: CNOTDecomposer) -> None:
    gate = SWAP(Qubit(4), Qubit(3))
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)
    assert decomposed_gate == [gate]


def test_ignores_double_controlled(decomposer: CNOTDecomposer) -> None:
    gate = ControlledGate(
        control_qubit=Qubit(5),
        target_gate=ControlledGate(control_qubit=Qubit(2), target_gate=X(Qubit(0))),
    )
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)
    assert decomposed_gate == [gate]


def test_preserves_CNOT(decomposer: CNOTDecomposer) -> None:
    gate = CNOT(Qubit(0), Qubit(1))
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)
    assert decomposed_gate == [CNOT(Qubit(0), Qubit(1))]


def test_CZ(decomposer: CNOTDecomposer) -> None:
    gate = CZ(Qubit(0), Qubit(1))
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)
    assert decomposed_gate == [
        Rz(Qubit(1), Float(math.pi)),
        Ry(Qubit(1), Float(math.pi / 2)),
        CNOT(Qubit(0), Qubit(1)),
        Ry(Qubit(1), Float(-math.pi / 2)),
        Rz(Qubit(1), Float(math.pi)),
    ]
