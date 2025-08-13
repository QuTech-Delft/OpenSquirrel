from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np
import pytest

from opensquirrel import CNOT, CR, X90, Y90, H, I, MinusX90, MinusY90, Rz, S, SDagger, X, Y, Z
from opensquirrel.ir.semantics import BlochSphereRotation
from opensquirrel.passes.decomposer import McKayDecomposer
from opensquirrel.passes.decomposer.general_decomposer import check_gate_replacement

if TYPE_CHECKING:
    from opensquirrel.ir import Gate


@pytest.fixture
def decomposer() -> McKayDecomposer:
    return McKayDecomposer()


@pytest.mark.parametrize(
    ("gate", "expected_result"),
    [(CNOT(0, 1), [CNOT(0, 1)]), (CR(2, 3, 2.123), [CR(2, 3, 2.123)])],
)
def test_ignores_2q_gates(decomposer: McKayDecomposer, gate: Gate, expected_result: list[Gate]) -> None:
    check_gate_replacement(gate, expected_result)
    assert decomposer.decompose(gate) == expected_result


def test_identity_decomposition(decomposer: McKayDecomposer) -> None:
    gate = I(0)
    decomposed_gate = decomposer.decompose(gate)
    expected_result = [I(0)]
    assert decomposed_gate == expected_result


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
    assert decomposed_gate == [Rz(0, math.pi), X90(0), X90(0)]


def test_z(decomposer: McKayDecomposer) -> None:
    gate = Z(0)
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)
    assert decomposed_gate == [Rz(0, math.pi)]


def test_rz(decomposer: McKayDecomposer) -> None:
    gate = Rz(0, math.pi / 2)
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)
    assert decomposed_gate == [Rz(0, math.pi / 2)]


def test_hadamard(decomposer: McKayDecomposer) -> None:
    gate = H(0)
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)
    assert decomposed_gate == [Rz(0, math.pi / 2), X90(0), Rz(0, math.pi / 2)]


def test_all_octants_of_bloch_sphere_rotation(decomposer: McKayDecomposer) -> None:
    steps = 6
    phase_steps = 3
    coordinates = np.linspace(-1, 1, num=steps)
    angles = np.linspace(-2 * np.pi, 2 * np.pi, num=steps)
    phases = np.linspace(-np.pi, np.pi, num=phase_steps)
    axes = [[i, j, z] for i in coordinates for j in coordinates for z in coordinates]

    for angle in angles:
        for axis in axes:
            for phase in phases:
                arbitrary_operation = BlochSphereRotation(qubit=0, axis=axis, angle=angle, phase=phase)
                decomposed_arbitrary_operation = decomposer.decompose(arbitrary_operation)
                check_gate_replacement(arbitrary_operation, decomposed_arbitrary_operation)


@pytest.mark.parametrize(
    ("gate", "expected_result"),
    [
        (I(0), [I(0)]),
        (X(0), [X90(0), X90(0)]),
        (Y(0), [Rz(0, math.pi), X90(0), X90(0)]),
        (Z(0), [Rz(0, math.pi)]),
        (
            BlochSphereRotation(
                qubit=0, axis=[1 / math.sqrt(3), 1 / math.sqrt(3), 1 / math.sqrt(3)], angle=2 * math.pi / 3, phase=0
            ),
            [X90(0), Rz(0, math.pi / 2)],
        ),
        (
            BlochSphereRotation(qubit=0, axis=[1, 1, 1], angle=-2 * math.pi / 3, phase=0),
            [X90(0), Rz(0, math.pi / 2), X90(0), Rz(0, math.pi / 2)],
        ),
        (
            BlochSphereRotation(qubit=0, axis=[-1, 1, 1], angle=2 * math.pi / 3, phase=0),
            [Rz(0, -math.pi / 2), X90(0), Rz(0, math.pi)],
        ),
        (
            BlochSphereRotation(qubit=0, axis=[-1, 1, 1], angle=-2 * math.pi / 3, phase=0),
            [Rz(0, -math.pi / 2), X90(0), Rz(0, math.pi / 2), X90(0), Rz(0, math.pi)],
        ),
        (BlochSphereRotation(qubit=0, axis=[1, -1, 1], angle=2 * math.pi / 3, phase=0), [Rz(0, math.pi / 2), X90(0)]),
        (
            BlochSphereRotation(qubit=0, axis=[1, -1, 1], angle=-2 * math.pi / 3, phase=0),
            [Rz(0, math.pi / 2), X90(0), Rz(0, math.pi / 2), X90(0)],
        ),
        (BlochSphereRotation(qubit=0, axis=[1, 1, -1], angle=2 * math.pi / 3, phase=0), [Rz(0, -math.pi / 2), X90(0)]),
        (
            BlochSphereRotation(
                qubit=0, axis=[1 / math.sqrt(3), 1 / math.sqrt(3), -1 / math.sqrt(3)], angle=-2 * math.pi / 3, phase=0
            ),
            [Rz(0, math.pi / 2), X90(0), Rz(0, math.pi / 2), X90(0), Rz(0, math.pi)],
        ),
        (X90(0), [X90(0)]),
        (MinusX90(0), [Rz(0, math.pi / 2), X90(0), Rz(0, math.pi / 2), X90(0), Rz(0, math.pi / 2)]),
        (Y90(0), [Rz(0, -math.pi / 2), X90(0), Rz(0, math.pi / 2)]),
        (MinusY90(0), [X90(0), Rz(0, math.pi / 2), X90(0), Rz(0, math.pi)]),
        (S(0), [Rz(0, math.pi / 2)]),
        (SDagger(0), [Rz(0, -math.pi / 2)]),
        (H(0), [Rz(0, math.pi / 2), X90(0), Rz(0, math.pi / 2)]),
        (
            BlochSphereRotation(qubit=0, axis=[1, 1, 0], angle=math.pi, phase=math.pi / 2),
            [Rz(0, -3 * math.pi / 4), X90(0), X90(0), Rz(0, -math.pi / 4)],
        ),
        (BlochSphereRotation(qubit=0, axis=[0, 1, 1], angle=math.pi, phase=math.pi / 2), [X90(0), Rz(0, math.pi)]),
        (
            BlochSphereRotation(qubit=0, axis=[-1, 1, 0], angle=math.pi, phase=math.pi / 2),
            [Rz(0, 3 * math.pi / 4), X90(0), X90(0), Rz(0, math.pi / 4)],
        ),
        (
            BlochSphereRotation(qubit=0, axis=[1, 0, -1], angle=math.pi, phase=math.pi / 2),
            [Rz(0, -math.pi / 2), X90(0), Rz(0, -math.pi / 2)],
        ),
        (BlochSphereRotation(qubit=0, axis=[0, -1, 1], angle=math.pi, phase=math.pi / 2), [Rz(0, math.pi), X90(0)]),
    ],
    ids=[
        "I",
        "X",
        "Y",
        "Z",
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "X90",
        "mX90",
        "Y90",
        "mY90",
        "Z90",
        "mZ90",
        "H1",
        "H2",
        "H3",
        "H4",
        "H5",
        "H6",
    ],
)
def test_single_qubit_clifford_gates(decomposer: McKayDecomposer, gate: Gate, expected_result: list[Gate]) -> None:
    decomposed_gates = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gates)
    assert decomposed_gates == expected_result
