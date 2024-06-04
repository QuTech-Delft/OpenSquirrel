import math

from opensquirrel.decomposer.zyz_decomposer import ZYZDecomposer
from opensquirrel.default_gates import CNOT, CR, H, Rx, Ry, Rz, S, Sdag, X, Y, Z
from opensquirrel.ir import BlochSphereRotation, Float, Qubit


def test_ignores_2q_gates() -> None:
    ZYZDecomposer().decompose(CNOT(Qubit(0), Qubit(1))) == [CNOT(Qubit(0), Qubit(1))]
    assert ZYZDecomposer().decompose(CR(Qubit(2), Qubit(3), Float(2.123))) == [CR(Qubit(2), Qubit(3), Float(2.123))]


def test_identity_empty_decomposition() -> None:
    assert ZYZDecomposer().decompose(BlochSphereRotation.identity(Qubit(0))) == []


def test_x() -> None:
    assert ZYZDecomposer().decompose(X(Qubit(0))) == [
        S(Qubit(0)),
        Ry(Qubit(0), Float(math.pi)),
        Sdag(Qubit(0)),
    ]


def test_x_arbitrary() -> None:
    assert ZYZDecomposer().decompose(Rx(Qubit(0), Float(0.9))) == [
        S(Qubit(0)),
        Ry(Qubit(0), Float(0.9)),
        Sdag(Qubit(0)),
    ]


def test_y() -> None:
    assert ZYZDecomposer().decompose(Y(Qubit(0))) == [Ry(Qubit(0), Float(math.pi))]


def test_y_arbitrary() -> None:
    assert ZYZDecomposer().decompose(Ry(Qubit(0), Float(0.9))) == [Ry(Qubit(0), Float(0.9))]


def test_z() -> None:
    assert ZYZDecomposer().decompose(Z(Qubit(0))) == [Rz(Qubit(0), Float(math.pi))]


def test_z_arbitrary() -> None:
    assert ZYZDecomposer().decompose(Rz(Qubit(0), Float(0.123))) == [Rz(Qubit(0), Float(0.123))]


def test_hadamard() -> None:
    assert ZYZDecomposer().decompose(H(Qubit(0))) == [Rz(Qubit(0), Float(math.pi)), Ry(Qubit(0), Float(math.pi / 2))]


def test_arbitrary() -> None:
    assert ZYZDecomposer().decompose(BlochSphereRotation(qubit=Qubit(0), angle=5.21, axis=(1, 2, 3), phase=0.324)) == [
        Rz(Qubit(0), Float(0.018644578210710527)),
        Ry(Qubit(0), Float(-0.6209410696845807)),
        Rz(Qubit(0), Float(-0.9086506397909061)),
    ]
