from __future__ import annotations

import math

import pytest

from opensquirrel.default_gates import CNOT, CZ, H, Ry, Rz, X
from opensquirrel.ir import ControlledGate, Float, Gate
from opensquirrel.passes.decomposer import CNOTDecomposer
from opensquirrel.passes.decomposer.general_decomposer import check_gate_replacement


@pytest.fixture(name="decomposer")
def decomposer_fixture() -> CNOTDecomposer:
    return CNOTDecomposer()


@pytest.mark.parametrize(
    ("gate", "expected_result"),
    [(H(0), [H(0)]), (Rz(0, Float(2.345)), [Rz(0, Float(2.345))])],
)
def test_ignores_1q_gates(decomposer: CNOTDecomposer, gate: Gate, expected_result: list[Gate]) -> None:
    check_gate_replacement(gate, expected_result)
    assert decomposer.decompose(gate) == expected_result


def test_ignores_double_controlled(decomposer: CNOTDecomposer) -> None:
    gate = ControlledGate(control_qubit=5, target_gate=ControlledGate(control_qubit=2, target_gate=X(0)))
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)
    assert decomposed_gate == [gate]


def test_preserves_CNOT(decomposer: CNOTDecomposer) -> None:  # noqa: N802
    gate = CNOT(0, 1)
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)
    assert decomposed_gate == [CNOT(0, 1)]


def test_CZ(decomposer: CNOTDecomposer) -> None:  # noqa: N802
    gate = CZ(0, 1)
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)
    assert decomposed_gate == [
        Rz(1, Float(math.pi)),
        Ry(1, Float(math.pi / 2)),
        CNOT(0, 1),
        Ry(1, Float(-math.pi / 2)),
        Rz(1, Float(math.pi)),
    ]
