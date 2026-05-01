from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pytest

from opensquirrel import CNOT, CR, CZ, SWAP, CRk, H, Ry
from opensquirrel.passes.decomposer import Can2CZDecomposer
from opensquirrel.passes.decomposer.general_decomposer import check_gate_decomposition

if TYPE_CHECKING:
    from opensquirrel.ir import Gate


@pytest.fixture
def decomposer() -> Can2CZDecomposer:
    return Can2CZDecomposer()


@pytest.mark.parametrize(
    ("gate", "expected_result"),
    [
        (H(0), [H(0)]),
        (Ry(0, 2.345), [Ry(0, 2.345)]),
    ],
    ids=["Hadamard", "rotation_gate"],
)
def test_ignores_1q_gates(decomposer: Can2CZDecomposer, gate: Gate, expected_result: list[Gate]) -> None:
    check_gate_decomposition(gate, expected_result)
    assert decomposer.decompose(gate) == expected_result


@pytest.mark.parametrize(
    ("gate", "expected_result"),
    [
        (CZ(0, 1), [CZ(0, 1)]),
        (CZ(1, 0), [CZ(1, 0)]),
    ],
    ids=["CZ_0_1", "CZ_1_0"],
)
def test_decomposes_CZ(decomposer: Can2CZDecomposer, gate: Gate, expected_result: list[Gate]) -> None:  # noqa: N802
    decomposed_gate = decomposer.decompose(gate)
    check_gate_decomposition(gate, decomposed_gate)
    assert decomposed_gate == expected_result


@pytest.mark.parametrize(
    ("gate", "expected_result"),
    [
        (CNOT(0, 1), [Ry(1, -math.pi / 2), CZ(0, 1), Ry(1, math.pi / 2)]),
        (CNOT(1, 0), [Ry(0, -math.pi / 2), CZ(1, 0), Ry(0, math.pi / 2)]),
    ],
    ids=["CNOT_0_1", "CNOT_1_0"],
)
def test_decomposes_CNOT(decomposer: Can2CZDecomposer, gate: Gate, expected_result: list[Gate]) -> None:  # noqa: N802
    decomposed_gate = decomposer.decompose(gate)
    check_gate_decomposition(gate, decomposed_gate)
    # assert decomposed_gate == expected_result
