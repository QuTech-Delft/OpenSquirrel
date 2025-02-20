from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pytest

from opensquirrel.ir import CNOT, CR, CZ, SWAP, CRk, H, Ry
from opensquirrel.passes.decomposer import SWAP2CZDecomposer
from opensquirrel.passes.decomposer.general_decomposer import check_gate_replacement

if TYPE_CHECKING:
    from opensquirrel.ir import Gate


@pytest.fixture(name="decomposer")
def decomposer_fixture() -> SWAP2CZDecomposer:
    return SWAP2CZDecomposer()


@pytest.mark.parametrize(
    ("gate", "expected_result"),
    [
        (H(0), [H(0)]),
        (Ry(0, 2.345), [Ry(0, 2.345)]),
    ],
    ids=["Hadamard", "rotation_gate"],
)
def test_ignores_1q_gates(decomposer: SWAP2CZDecomposer, gate: Gate, expected_result: list[Gate]) -> None:
    check_gate_replacement(gate, expected_result)
    assert decomposer.decompose(gate) == expected_result


@pytest.mark.parametrize(
    ("gate", "expected_result"),
    [
        (CNOT(0, 1), [CNOT(0, 1)]),
        (CR(0, 1, math.pi), [CR(0, 1, math.pi)]),
        (CRk(0, 1, 2), [CRk(0, 1, 2)]),
        (CZ(0, 1), [CZ(0, 1)]),
    ],
    ids=["CNOT_gate", "CR_gate", "CRk_gate", "CZ_gate"],
)
def test_ignores_2q_gates(decomposer: SWAP2CZDecomposer, gate: Gate, expected_result: list[Gate]) -> None:
    check_gate_replacement(gate, expected_result)
    assert decomposer.decompose(gate) == expected_result


@pytest.mark.parametrize(
    ("gate", "expected_result"),
    [
        (SWAP(0, 1), [
            Ry(1, -math.pi / 2),
            CZ(0, 1),
            Ry(1, math.pi / 2),
            Ry(0, -math.pi / 2),
            CZ(1, 0),
            Ry(0, math.pi / 2),
            Ry(1, -math.pi / 2),
            CZ(0, 1),
            Ry(1, math.pi / 2),
        ]),
        (SWAP(1, 0), [
            Ry(0, -math.pi / 2),
            CZ(1, 0),
            Ry(0, math.pi / 2),
            Ry(1, -math.pi / 2),
            CZ(0, 1),
            Ry(1, math.pi / 2),
            Ry(0, -math.pi / 2),
            CZ(1, 0),
            Ry(0, math.pi / 2),
        ]),
    ],
    ids=["SWAP_0_1", "SWAP_1_0"],
)
def test_decomposes_SWAP(decomposer: SWAP2CZDecomposer, gate: Gate, expected_result: list[Gate]) -> None:  # noqa: N802
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)
    assert decomposed_gate == expected_result
