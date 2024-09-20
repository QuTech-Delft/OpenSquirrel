from __future__ import annotations

import math
from collections.abc import Callable
from typing import SupportsFloat, SupportsInt

import numpy as np

from opensquirrel.ir import BlochSphereRotation, ControlledGate, Float, Gate, Int, MatrixGate, QubitLike, named_gate


@named_gate
def I(q: QubitLike) -> BlochSphereRotation:  # noqa: E743
    return BlochSphereRotation.identity(q)


@named_gate
def H(q: QubitLike) -> BlochSphereRotation:
    return BlochSphereRotation(qubit=q, axis=(1, 0, 1), angle=math.pi, phase=math.pi / 2)


@named_gate
def X(q: QubitLike) -> BlochSphereRotation:
    return BlochSphereRotation(qubit=q, axis=(1, 0, 0), angle=math.pi, phase=math.pi / 2)


@named_gate
def X90(q: QubitLike) -> BlochSphereRotation:
    return BlochSphereRotation(qubit=q, axis=(1, 0, 0), angle=math.pi / 2, phase=0)


@named_gate
def mX90(q: QubitLike) -> BlochSphereRotation:
    return BlochSphereRotation(qubit=q, axis=(1, 0, 0), angle=-math.pi / 2, phase=-0)


@named_gate
def Y(q: QubitLike) -> BlochSphereRotation:
    return BlochSphereRotation(qubit=q, axis=(0, 1, 0), angle=math.pi, phase=math.pi / 2)


@named_gate
def Y90(q: QubitLike) -> BlochSphereRotation:
    return BlochSphereRotation(qubit=q, axis=(0, 1, 0), angle=math.pi / 2, phase=0)


@named_gate
def mY90(q: QubitLike) -> BlochSphereRotation:
    return BlochSphereRotation(qubit=q, axis=(0, 1, 0), angle=-math.pi / 2, phase=0)


@named_gate
def Z(q: QubitLike) -> BlochSphereRotation:
    return BlochSphereRotation(qubit=q, axis=(0, 0, 1), angle=math.pi, phase=math.pi / 2)


@named_gate
def S(q: QubitLike) -> BlochSphereRotation:
    return BlochSphereRotation(qubit=q, axis=(0, 0, 1), angle=math.pi / 2, phase=0)


@named_gate
def Sdag(q: QubitLike) -> BlochSphereRotation:
    return BlochSphereRotation(qubit=q, axis=(0, 0, 1), angle=-math.pi / 2, phase=0)


@named_gate
def T(q: QubitLike) -> BlochSphereRotation:
    return BlochSphereRotation(qubit=q, axis=(0, 0, 1), angle=math.pi / 4, phase=0)


@named_gate
def Tdag(q: QubitLike) -> BlochSphereRotation:
    return BlochSphereRotation(qubit=q, axis=(0, 0, 1), angle=-math.pi / 4, phase=0)


@named_gate
def Rx(q: QubitLike, theta: SupportsFloat) -> BlochSphereRotation:
    return BlochSphereRotation(qubit=q, axis=(1, 0, 0), angle=theta, phase=0)


@named_gate
def Ry(q: QubitLike, theta: SupportsFloat) -> BlochSphereRotation:
    return BlochSphereRotation(qubit=q, axis=(0, 1, 0), angle=theta, phase=0)


@named_gate
def Rz(q: QubitLike, theta: SupportsFloat) -> BlochSphereRotation:
    return BlochSphereRotation(qubit=q, axis=(0, 0, 1), angle=theta, phase=0)


@named_gate
def CNOT(control: QubitLike, target: QubitLike) -> ControlledGate:
    return ControlledGate(control, X(target))


@named_gate
def CZ(control: QubitLike, target: QubitLike) -> ControlledGate:
    return ControlledGate(control, Z(target))


@named_gate
def CR(control: QubitLike, target: QubitLike, theta: SupportsFloat) -> ControlledGate:
    theta = Float(theta)
    return ControlledGate(
        control,
        BlochSphereRotation(qubit=target, axis=(0, 0, 1), angle=theta, phase=theta.value / 2),
    )


@named_gate
def CRk(control: QubitLike, target: QubitLike, k: SupportsInt) -> ControlledGate:
    theta = 2 * math.pi / (2 ** Int(k).value)
    return ControlledGate(control, BlochSphereRotation(qubit=target, axis=(0, 0, 1), angle=theta, phase=theta / 2))


@named_gate
def SWAP(q1: QubitLike, q2: QubitLike) -> MatrixGate:
    return MatrixGate(
        np.array(
            [
                [1, 0, 0, 0],
                [0, 0, 1, 0],
                [0, 1, 0, 0],
                [0, 0, 0, 1],
            ],
        ),
        [q1, q2],
    )


@named_gate
def sqrtSWAP(q1: QubitLike, q2: QubitLike) -> MatrixGate:
    return MatrixGate(
        np.array(
            [
                [1, 0, 0, 0],
                [0, (1 + 1j) / 2, (1 - 1j) / 2, 0],
                [0, (1 - 1j) / 2, (1 + 1j) / 2, 0],
                [0, 0, 0, 1],
            ],
        ),
        [q1, q2],
    )


@named_gate
def CCZ(control1: QubitLike, control2: QubitLike, target: QubitLike) -> ControlledGate:
    return ControlledGate(control1, CZ(control2, target))


default_bloch_sphere_rotations_without_params: list[Callable[[QubitLike], BlochSphereRotation]]
default_bloch_sphere_rotations_without_params = [
    I,
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
]
default_bloch_sphere_rotations: list[
    Callable[[QubitLike], BlochSphereRotation] | Callable[[QubitLike, SupportsFloat], BlochSphereRotation]
]
default_bloch_sphere_rotations = [
    *default_bloch_sphere_rotations_without_params,
    Rx,
    Ry,
    Rz,
]
default_gate_set: list[Callable[..., Gate]]
default_gate_set = [
    *default_bloch_sphere_rotations,
    CNOT,
    CZ,
    CR,
    CRk,
    SWAP,
    sqrtSWAP,
    CCZ,
]

default_gate_aliases = {
    "Hadamard": H,
    "Identity": I,
}
