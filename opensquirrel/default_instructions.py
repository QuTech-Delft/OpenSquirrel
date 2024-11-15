from __future__ import annotations

import math
from collections.abc import Callable
from typing import SupportsInt

from opensquirrel.ir import (
    Barrier,
    Bit,
    BlochSphereRotation,
    ControlledGate,
    Float,
    Gate,
    Int,
    Measure,
    NonGate,
    QubitLike,
    Reset,
    named_instruction,
)

######################
# Unitary instructions
######################


@named_instruction
def I(q: QubitLike) -> BlochSphereRotation:  # noqa: E743, N802
    return BlochSphereRotation.identity(q)


@named_instruction
def H(q: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=q, axis=(1, 0, 1), angle=math.pi, phase=math.pi / 2)


@named_instruction
def X(q: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=q, axis=(1, 0, 0), angle=math.pi, phase=math.pi / 2)


@named_instruction
def X90(q: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=q, axis=(1, 0, 0), angle=math.pi / 2, phase=0)


@named_instruction
def mX90(q: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=q, axis=(1, 0, 0), angle=-math.pi / 2, phase=-0)


@named_instruction
def Y(q: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=q, axis=(0, 1, 0), angle=math.pi, phase=math.pi / 2)


@named_instruction
def Y90(q: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=q, axis=(0, 1, 0), angle=math.pi / 2, phase=0)


@named_instruction
def mY90(q: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=q, axis=(0, 1, 0), angle=-math.pi / 2, phase=0)


@named_instruction
def Z(q: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=q, axis=(0, 0, 1), angle=math.pi, phase=math.pi / 2)


@named_instruction
def S(q: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=q, axis=(0, 0, 1), angle=math.pi / 2, phase=0)


@named_instruction
def Sdag(q: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=q, axis=(0, 0, 1), angle=-math.pi / 2, phase=0)


@named_instruction
def T(q: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=q, axis=(0, 0, 1), angle=math.pi / 4, phase=0)


@named_instruction
def Tdag(q: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=q, axis=(0, 0, 1), angle=-math.pi / 4, phase=0)


@named_instruction
def Rx(q: QubitLike, theta: Float) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=q, axis=(1, 0, 0), angle=theta.value, phase=0)


@named_instruction
def Ry(q: QubitLike, theta: Float) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=q, axis=(0, 1, 0), angle=theta.value, phase=0)


@named_instruction
def Rz(q: QubitLike, theta: Float) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=q, axis=(0, 0, 1), angle=theta.value, phase=0)


@named_instruction
def CNOT(control: QubitLike, target: QubitLike) -> ControlledGate:  # noqa: N802
    return ControlledGate(control, X(target))


@named_instruction
def CZ(control: QubitLike, target: QubitLike) -> ControlledGate:  # noqa: N802
    return ControlledGate(control, Z(target))


@named_instruction
def CR(control: QubitLike, target: QubitLike, theta: Float) -> ControlledGate:  # noqa: N802
    return ControlledGate(
        control,
        BlochSphereRotation(qubit=target, axis=(0, 0, 1), angle=theta.value, phase=theta.value / 2),
    )


@named_instruction
def CRk(control: QubitLike, target: QubitLike, k: SupportsInt) -> ControlledGate:  # noqa: N802
    theta = 2 * math.pi / (2 ** Int(k).value)
    return ControlledGate(control, BlochSphereRotation(qubit=target, axis=(0, 0, 1), angle=theta, phase=theta / 2))


##########################
# Non-unitary instructions
##########################


@named_instruction
def measure(q: QubitLike, b: Bit) -> Measure:
    return Measure(qubit=q, bit=b, axis=(0, 0, 1))


@named_instruction
def measure_z(q: QubitLike, b: Bit) -> Measure:
    return Measure(qubit=q, bit=b, axis=(0, 0, 1))


@named_instruction
def reset(q: QubitLike) -> Reset:
    return Reset(qubit=q)


@named_instruction
def barrier(q: QubitLike) -> Barrier:
    return Barrier(qubit=q)


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
    Callable[[QubitLike], BlochSphereRotation] | Callable[[QubitLike, Float], BlochSphereRotation]
]
default_bloch_sphere_rotations = [
    *default_bloch_sphere_rotations_without_params,
    Rx,
    Ry,
    Rz,
]
default_gate_set: list[Callable[..., Gate]]
default_gate_set = [*default_bloch_sphere_rotations, CNOT, CZ, CR, CRk]

default_gate_aliases = {
    "Hadamard": H,
    "Identity": I,
}

default_non_gate_set: list[Callable[..., NonGate]]
default_non_gate_set = [measure_z, measure, reset, barrier]
