from __future__ import annotations

import math
from typing import SupportsInt

from opensquirrel.ir import (
    Barrier,
    Bit,
    BlochSphereRotation,
    ControlledGate,
    Float,
    Int,
    Measure,
    QubitLike,
    Reset,
    named_gate,
    non_unitary,
)

######################
# Unitary instructions
######################


@named_gate
def I(q: QubitLike) -> BlochSphereRotation:  # noqa: E743, N802
    return BlochSphereRotation.identity(q)


@named_gate
def H(q: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=q, axis=(1, 0, 1), angle=math.pi, phase=math.pi / 2)


@named_gate
def X(q: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=q, axis=(1, 0, 0), angle=math.pi, phase=math.pi / 2)


@named_gate
def X90(q: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=q, axis=(1, 0, 0), angle=math.pi / 2, phase=0)


@named_gate
def mX90(q: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=q, axis=(1, 0, 0), angle=-math.pi / 2, phase=-0)


@named_gate
def Y(q: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=q, axis=(0, 1, 0), angle=math.pi, phase=math.pi / 2)


@named_gate
def Y90(q: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=q, axis=(0, 1, 0), angle=math.pi / 2, phase=0)


@named_gate
def mY90(q: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=q, axis=(0, 1, 0), angle=-math.pi / 2, phase=0)


@named_gate
def Z(q: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=q, axis=(0, 0, 1), angle=math.pi, phase=math.pi / 2)


@named_gate
def S(q: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=q, axis=(0, 0, 1), angle=math.pi / 2, phase=0)


@named_gate
def Sdag(q: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=q, axis=(0, 0, 1), angle=-math.pi / 2, phase=0)


@named_gate
def T(q: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=q, axis=(0, 0, 1), angle=math.pi / 4, phase=0)


@named_gate
def Tdag(q: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=q, axis=(0, 0, 1), angle=-math.pi / 4, phase=0)


@named_gate
def Rx(q: QubitLike, theta: Float) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=q, axis=(1, 0, 0), angle=theta.value, phase=0)


@named_gate
def Ry(q: QubitLike, theta: Float) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=q, axis=(0, 1, 0), angle=theta.value, phase=0)


@named_gate
def Rz(q: QubitLike, theta: Float) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=q, axis=(0, 0, 1), angle=theta.value, phase=0)


@named_gate
def CNOT(control: QubitLike, target: QubitLike) -> ControlledGate:  # noqa: N802
    return ControlledGate(control, X(target))


@named_gate
def CZ(control: QubitLike, target: QubitLike) -> ControlledGate:  # noqa: N802
    return ControlledGate(control, Z(target))


@named_gate
def CR(control: QubitLike, target: QubitLike, theta: Float) -> ControlledGate:  # noqa: N802
    return ControlledGate(
        control,
        BlochSphereRotation(qubit=target, axis=(0, 0, 1), angle=theta.value, phase=theta.value / 2),
    )


@named_gate
def CRk(control: QubitLike, target: QubitLike, k: SupportsInt) -> ControlledGate:  # noqa: N802
    theta = 2 * math.pi / (2 ** Int(k).value)
    return ControlledGate(control, BlochSphereRotation(qubit=target, axis=(0, 0, 1), angle=theta, phase=theta / 2))


##########################
# Non-unitary instructions
##########################


@non_unitary
def measure(q: QubitLike, b: Bit) -> Measure:
    return Measure(qubit=q, bit=b, axis=(0, 0, 1))


@non_unitary
def measure_z(q: QubitLike, b: Bit) -> Measure:
    return Measure(qubit=q, bit=b, axis=(0, 0, 1))


@non_unitary
def reset(q: QubitLike) -> Reset:
    return Reset(qubit=q)


@non_unitary
def barrier(q: QubitLike) -> Barrier:
    return Barrier(qubit=q)


default_bloch_sphere_rotation_without_params_set = {
    "H": H,
    "I": I,
    "S": S,
    "Sdag": Sdag,
    "T": T,
    "Tdag": Tdag,
    "X": X,
    "X90": X90,
    "Y": Y,
    "Y90": Y90,
    "Z": Z,
    "mX90": mX90,
    "mY90": mY90,
}
default_bloch_sphere_rotation_set = {
    **default_bloch_sphere_rotation_without_params_set,
    "Rx": Rx,
    "Ry": Ry,
    "Rz": Rz,
}
default_controlled_gate_set = {
    "CNOT": CNOT,
    "CR": CR,
    "CRk": CRk,
    "CZ": CZ,
}
default_gate_alias_set = {
    "Hadamard": H,
    "Identity": I,
}
default_gate_set = {
    **default_bloch_sphere_rotation_set,
    **default_controlled_gate_set,
    **default_gate_alias_set,
}
default_unitary_set = {**default_gate_set}
default_non_unitary_set = {
    "barrier": barrier,
    "measure": measure,
    "measure_z": measure_z,
    "reset": reset,
}
default_instructions = {
    **default_unitary_set,
    **default_non_unitary_set,
}
