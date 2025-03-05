from __future__ import annotations

import math

import pytest

from opensquirrel import CNOT, CZ, H, Ry, Rz, X
from opensquirrel.ir import ControlledGate, Gate
from opensquirrel.passes.decomposer import CZDecomposer
from opensquirrel.passes.decomposer.general_decomposer import check_gate_replacement


@pytest.fixture(name="decomposer")
def decomposer_fixture() -> CZDecomposer:
    return CZDecomposer()


@pytest.mark.parametrize(("gate", "expected_result"), [(H(0), [H(0)]), (Rz(0, 2.345), [Rz(0, 2.345)])])
def test_ignores_1q_gates(decomposer: CZDecomposer, gate: Gate, expected_result: list[Gate]) -> None:
    check_gate_replacement(gate, expected_result)
    assert decomposer.decompose(gate) == expected_result


def test_ignores_double_controlled(decomposer: CZDecomposer) -> None:
    gate = ControlledGate(control_qubit=5, target_gate=ControlledGate(control_qubit=2, target_gate=X(0)))
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)
    assert decomposed_gate == [gate]


def test_preserves_CZ(decomposer: CZDecomposer) -> None:  # noqa: N802
    gate = CZ(0, 1)
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)
    assert decomposed_gate == [CZ(0, 1)]


def test_CNOT(decomposer: CZDecomposer) -> None:  # noqa: N802
    gate = CNOT(0, 1)
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)

    assert decomposed_gate == [Rz(1, math.pi), Ry(1, math.pi / 2), CZ(0, 1), Rz(1, math.pi), Ry(1, math.pi / 2)]
