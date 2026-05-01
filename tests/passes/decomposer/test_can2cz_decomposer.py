from __future__ import annotations

from math import pi
from typing import TYPE_CHECKING

import numpy as np
import pytest

from opensquirrel import CNOT, CR, CZ, SWAP, CRk, H, Ry
from opensquirrel.ir.semantics.bsr import BlochSphereRotation
from opensquirrel.ir.semantics.canonical_gate import CanonicalGateSemantic
from opensquirrel.ir.semantics.controlled_gate import ControlledGateSemantic
from opensquirrel.ir.semantics.matrix_gate import MatrixGateSemantic
from opensquirrel.ir.two_qubit_gate import TwoQubitGate
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
        (CNOT(0, 1), [Ry(1, -pi / 2), CZ(0, 1), Ry(1, pi / 2)]),
        (CNOT(1, 0), [Ry(0, -pi / 2), CZ(1, 0), Ry(0, pi / 2)]),
    ],
    ids=["CNOT_0_1", "CNOT_1_0"],
)
def test_decomposes_CNOT(decomposer: Can2CZDecomposer, gate: Gate, expected_result: list[Gate]) -> None:  # noqa: N802
    decomposed_gate = decomposer.decompose(gate)
    check_gate_decomposition(gate, decomposed_gate)
    assert decomposed_gate == expected_result


@pytest.mark.parametrize(
    "gate",
    [
        CRk(0, 1, 2),
        CRk(1, 0, 2),
        CR(0, 1, pi / 3),
        CR(1, 0, pi / 3),
        SWAP(0, 1),
        SWAP(1, 0),
    ],
    ids=["CRk_0_1_2", "CRk_1_0_2", "CR_0_1_pi_3", "CR_1_0_pi_3", "SWAP_0_1", "SWAP_1_0"],
)
def test_decomposes_known_two_qubit_gates(decomposer: Can2CZDecomposer, gate: Gate) -> None:
    decomposed_gate = decomposer.decompose(gate)
    check_gate_decomposition(gate, decomposed_gate)


@pytest.mark.parametrize(
    "gate",
    [
        TwoQubitGate(
            qubit0=0,
            qubit1=1,
            gate_semantic=CanonicalGateSemantic(
                axis=(0.3, 0.2, 0.1),
                rotations=[
                    BlochSphereRotation((0, 1, 0), 0.4 * pi, 0.2 * pi),
                    BlochSphereRotation((1, 0, 0), 0.5 * pi, 0.25 * pi),
                    BlochSphereRotation((1, 0, 0), 0.2 * pi, 0.1 * pi),
                    BlochSphereRotation((0, 0, 1), 0.3 * pi, 0.15 * pi),
                    ]
                )
        ),
        TwoQubitGate(
            qubit0=0,
            qubit1=1,
            gate_semantic=ControlledGateSemantic(
                target_bsr=BlochSphereRotation((0, 1, 0), pi / 5, pi / 10)
            )
        ),
        TwoQubitGate(
            qubit0=0,
            qubit1=1,
            gate_semantic=MatrixGateSemantic(
                matrix= (1 / 2) * np.array(
                    [
                        [1,  1,  1,  1],
                        [1, -1,  1, -1],
                        [1,  1, -1, -1],
                        [1, -1, -1,  1],
                    ],
                    dtype=np.complex128,
                )
            )
        ),      
    ],
    ids=["canonical", "controlled", "matrix"],
)
def test_decomposes_other_two_qubit_gate_semantics(decomposer: Can2CZDecomposer, gate: Gate) -> None:
    decomposed_gate = decomposer.decompose(gate)
    check_gate_decomposition(gate, decomposed_gate)
