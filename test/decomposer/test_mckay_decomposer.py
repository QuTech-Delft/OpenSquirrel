import math

import pytest

from opensquirrel.decomposer.general_decomposer import check_gate_replacement
from opensquirrel.decomposer.mckay_decomposer import McKayDecomposer
from opensquirrel.default_gates import CNOT, CR, X90, H, I, Rz, X, Y, Z
from opensquirrel.ir import BlochSphereRotation, Float, Gate, Qubit


@pytest.fixture(name="decomposer")
def decomposer_fixture() -> McKayDecomposer:
    return McKayDecomposer()


@pytest.mark.parametrize(
    "gate,expected_result",
    [
        (CNOT(Qubit(0), Qubit(1)), [CNOT(Qubit(0), Qubit(1))]),
        (CR(Qubit(2), Qubit(3), Float(2.123)), [CR(Qubit(2), Qubit(3), Float(2.123))]),
    ],
)
def test_ignores_2q_gates(decomposer: McKayDecomposer, gate: Gate, expected_result: list[Gate]) -> None:
    check_gate_replacement(gate, expected_result)
    assert decomposer.decompose(gate) == expected_result


def test_identity_empty_decomposition(decomposer: McKayDecomposer) -> None:
    gate = I(Qubit(0))
    decomposed_gate = decomposer.decompose(gate)
    assert decomposed_gate == []


def test_x(decomposer: McKayDecomposer) -> None:
    gate = X(Qubit(0))
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)
    expected_result = [
        X90(Qubit(0)),
        X90(Qubit(0)),
    ]
    assert decomposed_gate == expected_result


def test_y(decomposer: McKayDecomposer) -> None:
    gate = Y(Qubit(0))
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)
    assert decomposed_gate == [Rz(Qubit(0), Float(math.pi)), X90(Qubit(0)), X90(Qubit(0))]


def test_z(decomposer: McKayDecomposer) -> None:
    gate = Z(Qubit(0))
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)
    assert decomposed_gate == [Rz(Qubit(0), Float(math.pi))]


def test_rz(decomposer: McKayDecomposer) -> None:
    gate = Rz(Qubit(0), Float(math.pi / 2))
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)
    assert decomposed_gate == [Rz(Qubit(0), Float(math.pi / 2))]


def test_hadamard(decomposer: McKayDecomposer) -> None:
    gate = H(Qubit(0))
    decomposed_gate = decomposer.decompose(gate)
    check_gate_replacement(gate, decomposed_gate)
    print(decomposed_gate)
    assert decomposed_gate == [
        Rz(Qubit(0), Float(math.pi / 2)),
        X90(Qubit(0)),
        Rz(Qubit(0), Float(math.pi / 2)),
    ]


def test_arbitrary(decomposer: McKayDecomposer) -> None:
    arbitrary_operation = BlochSphereRotation(qubit=Qubit(0), angle=5.21, axis=(1, 2, 3), phase=0.324)
    decomposed_arbitrary_operation = decomposer.decompose(arbitrary_operation)
    check_gate_replacement(arbitrary_operation, decomposed_arbitrary_operation)
    assert decomposed_arbitrary_operation == [
        Rz(Qubit(0), Float(0.018644578210707863)),
        X90(Qubit(0)),
        Rz(Qubit(0), Float(2.520651583905213)),
        X90(Qubit(0)),
        Rz(Qubit(0), Float(2.2329420137988887)),
    ]
