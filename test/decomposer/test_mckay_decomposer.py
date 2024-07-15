import math

import pytest

from opensquirrel.decomposer.mckay_decomposer import McKayDecomposer
from opensquirrel.default_gates import CNOT, CR, X90, Y90, H, Rz, X, Y, Z
from opensquirrel.ir import BlochSphereRotation, Float, Qubit


@pytest.fixture(name="decomposer")
def decomposer_fixture() -> McKayDecomposer:
    return McKayDecomposer()


def test_ignores_2q_gates(decomposer: McKayDecomposer) -> None:
    assert decomposer.decompose(CNOT(Qubit(0), Qubit(1))) == [CNOT(Qubit(0), Qubit(1))]
    assert decomposer.decompose(CR(Qubit(2), Qubit(3), Float(2.123))) == [CR(Qubit(2), Qubit(3), Float(2.123))]


def test_identity_empty_decomposition(decomposer: McKayDecomposer) -> None:
    assert decomposer.decompose(BlochSphereRotation.identity(Qubit(0))) == []


def test_x(decomposer: McKayDecomposer) -> None:
    assert decomposer.decompose(X(Qubit(0))) == [
        X90(Qubit(0)),
        X90(Qubit(0)),
    ]


def test_y(decomposer: McKayDecomposer) -> None:
    assert decomposer.decompose(Y(Qubit(0))) == [Rz(Qubit(0), Float(math.pi)), X90(Qubit(0)), X90(Qubit(0))]


def test_z(decomposer: McKayDecomposer) -> None:
    assert decomposer.decompose(Z(Qubit(0))) == [Rz(Qubit(0), Float(math.pi))]


def test_rz(decomposer: McKayDecomposer) -> None:
    assert decomposer.decompose(Rz(Qubit(0), Float(math.pi / 2))) == [Rz(Qubit(0), Float(math.pi / 2))]


def test_hadamard(decomposer: McKayDecomposer) -> None:
    assert decomposer.decompose(H(Qubit(0))) == [
        BlochSphereRotation(Qubit(0), axis=(0, 0, 1), angle=math.pi / 2, phase=0.0),
        BlochSphereRotation(Qubit(0), axis=(1, 0, 0), angle=math.pi / 2, phase=0.0),
        BlochSphereRotation(Qubit(0), axis=(0, 0, 1), angle=math.pi / 2, phase=0.0),
    ]


def test_arbitrary(decomposer: McKayDecomposer) -> None:
    assert decomposer.decompose(BlochSphereRotation(qubit=Qubit(0), angle=5.21, axis=(1, 2, 3), phase=0.324)) == [
        Rz(Qubit(0), Float(0.018644578210707863)),
        X90(Qubit(0)),
        Rz(Qubit(0), Float(2.520651583905213)),
        X90(Qubit(0)),
        Rz(Qubit(0), Float(2.2329420137988887)),
    ]
