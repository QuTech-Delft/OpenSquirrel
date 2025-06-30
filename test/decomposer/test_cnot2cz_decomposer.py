from __future__ import annotations

import math

import pytest

from opensquirrel.ir import CNOT, CR, CZ, SWAP, ControlledGate, CRk, Gate, H, Ry, X
from opensquirrel.passes.decomposer import CNOT2CZDecomposer
from opensquirrel.passes.decomposer.general_decomposer import check_gate_replacement


@pytest.fixture(name="decomposer")
def decomposer_fixture() -> CNOT2CZDecomposer:
    return CNOT2CZDecomposer()


@pytest.mark.parametrize(
    ("gate", "expected_result"),
    [
        (H(0), [H(0)]),
        (Ry(0, 2.345), [Ry(0, 2.345)]),
    ],
    ids=["Hadamard", "rotation_gate"],
)
def test_ignores_1q_gates(decomposer: CNOT2CZDecomposer, gate: Gate, expected_result: list[Gate]) -> None:
    check_gate_replacement(gate, expected_result)
    assert decomposer.decompose(gate) == expected_result


@pytest.mark.parametrize(
    ("gate", "expected_result"),
    [
        (CR(0, 1, math.pi), [CR(0, 1, math.pi)]),
        (CRk(0, 1, 2), [CRk(0, 1, 2)]),
        (CZ(0, 1), [CZ(0, 1)]),
        (SWAP(0, 1), [SWAP(0, 1)]),
    ],
    ids=["CR_gate", "CRk_gate", "CZ_gate", "SWAP_gate"],
)
def test_ignores_2q_gates(decomposer: CNOT2CZDecomposer, gate: Gate, expected_result: list[Gate]) -> None:
    check_gate_replacement(gate, expected_result)
    assert decomposer.decompose(gate) == expected_result


def test_ignores_double_controlled(decomposer: CNOT2CZDecomposer) -> None:
    gate = ControlledGate(control_qubit=5, target_gate=ControlledGate(control_qubit=2, target_gate=X(0)))
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)
    assert decomposed_gate == [gate]


@pytest.mark.parametrize(
    ("gate", "expected_result"),
    [
        (CNOT(0, 1), [Ry(1, -math.pi / 2), CZ(0, 1), Ry(1, math.pi / 2)]),
        (CNOT(1, 0), [Ry(0, -math.pi / 2), CZ(1, 0), Ry(0, math.pi / 2)]),
    ],
    ids=["CNOT_0_1", "CNOT_1_0"],
)
def test_decomposes_CNOT(decomposer: CNOT2CZDecomposer, gate: Gate, expected_result: list[Gate]) -> None:  # noqa: N802
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)
    assert decomposed_gate == expected_result
