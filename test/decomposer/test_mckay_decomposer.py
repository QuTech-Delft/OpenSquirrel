from __future__ import annotations

import math

import numpy as np
import pytest

from opensquirrel.default_instructions import CNOT, CR, X90, H, I, Rz, X, Y, Z
from opensquirrel.ir import BlochSphereRotation, Float, Gate
from opensquirrel.passes.decomposer import McKayDecomposer
from opensquirrel.passes.decomposer.general_decomposer import check_gate_replacement


@pytest.fixture(name="decomposer")
def decomposer_fixture() -> McKayDecomposer:
    return McKayDecomposer()


@pytest.mark.parametrize(
    ("gate", "expected_result"),
    [(CNOT(0, 1), [CNOT(0, 1)]), (CR(2, 3, Float(2.123)), [CR(2, 3, Float(2.123))])],
)
def test_ignores_2q_gates(decomposer: McKayDecomposer, gate: Gate, expected_result: list[Gate]) -> None:
    check_gate_replacement(gate, expected_result)
    assert decomposer.decompose(gate) == expected_result


def test_identity_empty_decomposition(decomposer: McKayDecomposer) -> None:
    gate = I(0)
    decomposed_gate = decomposer.decompose(gate)
    assert decomposed_gate == []


def test_x(decomposer: McKayDecomposer) -> None:
    gate = X(0)
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)
    expected_result = [X90(0), X90(0)]
    assert decomposed_gate == expected_result


def test_y(decomposer: McKayDecomposer) -> None:
    gate = Y(0)
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)
    assert decomposed_gate == [Rz(0, Float(math.pi)), X90(0), X90(0)]


def test_z(decomposer: McKayDecomposer) -> None:
    gate = Z(0)
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)
    assert decomposed_gate == [Rz(0, Float(math.pi))]


def test_rz(decomposer: McKayDecomposer) -> None:
    gate = Rz(0, Float(math.pi / 2))
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)
    assert decomposed_gate == [Rz(0, Float(math.pi / 2))]


def test_hadamard(decomposer: McKayDecomposer) -> None:
    gate = H(0)
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)
    assert decomposed_gate == [Rz(0, Float(math.pi / 2)), X90(0), Rz(0, Float(math.pi / 2))]


def test_arbitrary(decomposer: McKayDecomposer) -> None:
    arbitrary_operation = BlochSphereRotation(qubit=0, angle=5.21, axis=(1, 2, 3), phase=0.324)
    decomposed_arbitrary_operation = decomposer.decompose(arbitrary_operation)
    check_gate_replacement(arbitrary_operation, decomposed_arbitrary_operation)
    assert decomposed_arbitrary_operation == [
        Rz(0, Float(0.018644578210707863)),
        X90(0),
        Rz(0, Float(2.520651583905213)),
        X90(0),
        Rz(0, Float(2.2329420137988887)),
    ]


def test_all_octants_of_bloch_sphere_rotation(decomposer: McKayDecomposer) -> None:
    steps = 6
    coordinates = np.linspace(-1, 1, num=steps)
    angles = np.linspace(-2 * np.pi, 2 * np.pi, num=steps)
    axis_list = [[i, j, z] for i in coordinates for j in coordinates for z in coordinates]

    for angle in angles:
        for axis in axis_list:
            arbitrary_operation = BlochSphereRotation(qubit=0, axis=axis, angle=angle, phase=0.0)
            decomposed_arbitrary_operation = decomposer.decompose(arbitrary_operation)
            check_gate_replacement(arbitrary_operation, decomposed_arbitrary_operation)
