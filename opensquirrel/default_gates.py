import math

import numpy as np

from opensquirrel.squirrel_ir import BlochSphereRotation, ControlledGate, Float, Int, MatrixGate, Qubit, named_gate


@named_gate
def H(q: Qubit) -> BlochSphereRotation:
    return BlochSphereRotation(qubit=q, axis=(1, 0, 1), angle=math.pi, phase=math.pi / 2)


@named_gate
def X(q: Qubit) -> BlochSphereRotation:
    return BlochSphereRotation(qubit=q, axis=(1, 0, 0), angle=math.pi, phase=math.pi / 2)


@named_gate
def X90(q: Qubit) -> BlochSphereRotation:
    return BlochSphereRotation(qubit=q, axis=(1, 0, 0), angle=math.pi / 2, phase=0)


@named_gate
def mX90(q: Qubit) -> BlochSphereRotation:
    return BlochSphereRotation(qubit=q, axis=(1, 0, 0), angle=-math.pi / 2, phase=-0)


@named_gate
def Y(q: Qubit) -> BlochSphereRotation:
    return BlochSphereRotation(qubit=q, axis=(0, 1, 0), angle=math.pi, phase=math.pi / 2)


@named_gate
def Y90(q: Qubit) -> BlochSphereRotation:
    return BlochSphereRotation(qubit=q, axis=(0, 1, 0), angle=math.pi / 2, phase=0)


@named_gate
def mY90(q: Qubit) -> BlochSphereRotation:
    return BlochSphereRotation(qubit=q, axis=(0, 1, 0), angle=-math.pi / 2, phase=0)


@named_gate
def Z(q: Qubit) -> BlochSphereRotation:
    return BlochSphereRotation(qubit=q, axis=(0, 0, 1), angle=math.pi, phase=math.pi / 2)


@named_gate
def S(q: Qubit) -> BlochSphereRotation:
    return BlochSphereRotation(qubit=q, axis=(0, 0, 1), angle=math.pi / 2, phase=0)


@named_gate
def Sdag(q: Qubit) -> BlochSphereRotation:
    return BlochSphereRotation(qubit=q, axis=(0, 0, 1), angle=-math.pi / 2, phase=0)


@named_gate
def T(q: Qubit) -> BlochSphereRotation:
    return BlochSphereRotation(qubit=q, axis=(0, 0, 1), angle=math.pi / 4, phase=0)


@named_gate
def Tdag(q: Qubit) -> BlochSphereRotation:
    return BlochSphereRotation(qubit=q, axis=(0, 0, 1), angle=-math.pi / 4, phase=0)


@named_gate
def Rx(q: Qubit, theta: Float) -> BlochSphereRotation:
    return BlochSphereRotation(qubit=q, axis=(1, 0, 0), angle=theta.value, phase=0)


@named_gate
def Ry(q: Qubit, theta: Float) -> BlochSphereRotation:
    return BlochSphereRotation(qubit=q, axis=(0, 1, 0), angle=theta.value, phase=0)


@named_gate
def Rz(q: Qubit, theta: Float) -> BlochSphereRotation:
    return BlochSphereRotation(qubit=q, axis=(0, 0, 1), angle=theta.value, phase=0)


@named_gate
def CNOT(control: Qubit, target: Qubit) -> ControlledGate:
    return ControlledGate(control, X(target))


@named_gate
def CZ(control: Qubit, target: Qubit) -> ControlledGate:
    return ControlledGate(control, Z(target))


@named_gate
def CR(control: Qubit, target: Qubit, theta: Float) -> ControlledGate:
    return ControlledGate(
        control, BlochSphereRotation(qubit=target, axis=(0, 0, 1), angle=theta.value, phase=theta.value / 2)
    )


@named_gate
def CRk(control: Qubit, target: Qubit, k: Int) -> ControlledGate:
    theta = 2 * math.pi / (2**k.value)
    return ControlledGate(control, BlochSphereRotation(qubit=target, axis=(0, 0, 1), angle=theta, phase=theta / 2))


@named_gate
def SWAP(q1: Qubit, q2: Qubit) -> MatrixGate:
    return MatrixGate(
        np.array(
            [
                [1, 0, 0, 0],
                [0, 0, 1, 0],
                [0, 1, 0, 0],
                [0, 0, 0, 1],
            ]
        ),
        [q1, q2],
    )


@named_gate
def sqrtSWAP(q1: Qubit, q2: Qubit) -> MatrixGate:
    return MatrixGate(
        np.array(
            [
                [1, 0, 0, 0],
                [0, (1 + 1j) / 2, (1 - 1j) / 2, 0],
                [0, (1 - 1j) / 2, (1 + 1j) / 2, 0],
                [0, 0, 0, 1],
            ]
        ),
        [q1, q2],
    )


@named_gate
def CCZ(control1: Qubit, control2: Qubit, target: Qubit) -> ControlledGate:
    return ControlledGate(control1, CZ(control2, target))


default_gate_set = [
    H,
    X,
    X90,
    mX90,
    Y,
    Y90,
    mY90,
    Z,
    S,
    Sdag,
    T,
    Tdag,
    Rx,
    Ry,
    Rz,
    CNOT,
    CZ,
    CR,
    CRk,
    SWAP,
    sqrtSWAP,
    CCZ,
]

default_gate_aliases = {"Hadamard": H}
