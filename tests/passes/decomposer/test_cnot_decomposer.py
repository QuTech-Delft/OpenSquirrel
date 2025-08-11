from __future__ import annotations

from math import pi, sqrt

import pytest

from opensquirrel import CNOT, CR, CZ, CRk, H, Ry, Rz, X
from opensquirrel.ir import ControlledGate, Gate
from opensquirrel.passes.decomposer import CNOTDecomposer
from opensquirrel.passes.decomposer.general_decomposer import check_gate_replacement


@pytest.fixture
def decomposer() -> CNOTDecomposer:
    return CNOTDecomposer()


@pytest.mark.parametrize(("gate", "expected_result"), [(H(0), [H(0)]), (Rz(0, 2.345), [Rz(0, 2.345)])])
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
    assert decomposed_gate == [Rz(1, pi), Ry(1, pi / 2), CNOT(0, 1), Ry(1, -pi / 2), Rz(1, pi)]


@pytest.mark.parametrize(
    "controlled_gate",
    [
        CR(0, 1, pi / 2),
        CR(0, 1, pi / 4),
        CR(0, 1, 1 / sqrt(2)),
        CRk(0, 1, 1),
        CRk(0, 1, 2),
        CRk(0, 1, 16),
    ],
    ids=["CR_1", "CR_2", "CR_3", "CRk_1", "CRk_2", "CRk_3"],
)
def test_controlled_gates(decomposer: CNOTDecomposer, controlled_gate: ControlledGate) -> None:
    decomposed_gate = decomposer.decompose(controlled_gate)
    check_gate_replacement(controlled_gate, decomposed_gate)
