from __future__ import annotations

from math import pi
from typing import TYPE_CHECKING

import numpy as np
import pytest

from opensquirrel import CCX, CNOT, CSWAP, CZ, SWAP, H, Ry, TDagger
from opensquirrel.circuit_matrix_calculator import get_circuit_matrix
from opensquirrel.passes.decomposer import ThreeQubitGateDecomposer
from opensquirrel.passes.decomposer.general_decomposer import check_gate_decomposition
from opensquirrel.reindexer import get_reindexed_circuit

if TYPE_CHECKING:
    from opensquirrel.ir import Gate


@pytest.fixture
def decomposer() -> ThreeQubitGateDecomposer:
    return ThreeQubitGateDecomposer()


@pytest.mark.parametrize(
    ("gate", "expected_result"),
    [
        (H(0), [H(0)]),
        (Ry(0, 2.345), [Ry(0, 2.345)]),
    ],
    ids=["Hadamard", "rotation_gate"],
)
def test_ignores_1q_gates(decomposer: ThreeQubitGateDecomposer, gate: Gate, expected_result: list[Gate]) -> None:
    check_gate_decomposition(gate, expected_result)
    assert decomposer.decompose(gate) == expected_result


@pytest.mark.parametrize(
    ("gate", "expected_result"),
    [
        (CNOT(0, 1), [CNOT(0, 1)]),
        (CZ(0, 1), [CZ(0, 1)]),
        (SWAP(0, 1), [SWAP(0, 1)]),
    ],
    ids=["CNOT_gate", "CZ_gate", "SWAP_gate"],
)
def test_ignores_2q_gates(decomposer: ThreeQubitGateDecomposer, gate: Gate, expected_result: list[Gate]) -> None:
    check_gate_decomposition(gate, expected_result)
    assert decomposer.decompose(gate) == expected_result


@pytest.mark.parametrize(
    "gate",
    [CCX(0, 1, 2), CCX(2, 0, 1), CCX(1, 2, 0), CSWAP(0, 1, 2), CSWAP(2, 0, 1), CSWAP(1, 2, 0)],
    ids=["CCX_0_1_2", "CCX_2_0_1", "CCX_1_2_0", "CSWAP_0_1_2", "CSWAP_2_0_1", "CSWAP_1_2_0"],
)
def test_decomposition_is_valid(decomposer: ThreeQubitGateDecomposer, gate: Gate) -> None:
    decomposed_gate = decomposer.decompose(gate)
    check_gate_decomposition(gate, decomposed_gate)


@pytest.mark.parametrize(
    "gate",
    [CCX(0, 1, 2), CSWAP(0, 1, 2)],
    ids=["CCX", "CSWAP"],
)
def test_decomposition_preserves_global_phase(decomposer: ThreeQubitGateDecomposer, gate: Gate) -> None:
    qubit_indices = gate.qubit_indices
    original_matrix = get_circuit_matrix(get_reindexed_circuit([gate], qubit_indices))
    decomposed_matrix = get_circuit_matrix(get_reindexed_circuit(decomposer.decompose(gate), qubit_indices))
    np.testing.assert_allclose(original_matrix, decomposed_matrix, atol=1e-12)


@pytest.mark.parametrize(
    ("gate", "expected_cz_count"),
    [(CCX(0, 1, 2), 6), (CSWAP(0, 1, 2), 8)],
    ids=["CCX", "CSWAP"],
)
def test_decomposition_uses_expected_number_of_cz_gates(
    decomposer: ThreeQubitGateDecomposer, gate: Gate, expected_cz_count: int
) -> None:
    decomposed_gate = decomposer.decompose(gate)
    assert sum(1 for g in decomposed_gate if g.name == "CZ") == expected_cz_count


@pytest.mark.parametrize(
    "gate",
    [CCX(0, 1, 2), CSWAP(0, 1, 2)],
    ids=["CCX", "CSWAP"],
)
def test_decomposition_yields_only_cz_and_single_qubit_gates(decomposer: ThreeQubitGateDecomposer, gate: Gate) -> None:
    for decomposed_gate in decomposer.decompose(gate):
        assert len(decomposed_gate.qubit_operands) == 1 or decomposed_gate.name == "CZ"


def test_decomposes_CCX(decomposer: ThreeQubitGateDecomposer) -> None:  # noqa: N802
    assert decomposer.decompose(CCX(0, 1, 2))[:5] == [
        Ry(2, -pi / 2),
        Ry(2, -pi / 2),
        CZ(1, 2),
        Ry(2, pi / 2),
        TDagger(2),
    ]
