from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Callable, SupportsFloat, SupportsInt

import numpy as np

from opensquirrel.ir import (
    Barrier,
    BitLike,
    BlochSphereRotation,
    ControlledGate,
    Gate,
    Init,
    Instruction,
    MatrixGate,
    Measure,
    NonUnitary,
    QubitLike,
    Reset,
    Unitary,
    Wait,
    named_gate,
    non_unitary,
)

######################
# Unitary instructions
######################


@named_gate
def I(qubit: QubitLike) -> BlochSphereRotation:  # noqa: E743, N802
    return BlochSphereRotation(qubit=qubit, axis=(1, 0, 0), angle=0, phase=0)


@named_gate
def H(qubit: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=qubit, axis=(1, 0, 1), angle=math.pi, phase=math.pi / 2)


@named_gate
def X(qubit: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=qubit, axis=(1, 0, 0), angle=math.pi, phase=math.pi / 2)


@named_gate
def X90(qubit: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=qubit, axis=(1, 0, 0), angle=math.pi / 2, phase=0)


@named_gate
def mX90(qubit: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=qubit, axis=(1, 0, 0), angle=-math.pi / 2, phase=-0)


@named_gate
def Y(qubit: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=qubit, axis=(0, 1, 0), angle=math.pi, phase=math.pi / 2)


@named_gate
def Y90(qubit: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=qubit, axis=(0, 1, 0), angle=math.pi / 2, phase=0)


@named_gate
def mY90(qubit: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=qubit, axis=(0, 1, 0), angle=-math.pi / 2, phase=0)


@named_gate
def Z(qubit: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=qubit, axis=(0, 0, 1), angle=math.pi, phase=math.pi / 2)


@named_gate
def S(qubit: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=qubit, axis=(0, 0, 1), angle=math.pi / 2, phase=0)


@named_gate
def Sdag(qubit: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=qubit, axis=(0, 0, 1), angle=-math.pi / 2, phase=0)


@named_gate
def T(qubit: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=qubit, axis=(0, 0, 1), angle=math.pi / 4, phase=0)


@named_gate
def Tdag(qubit: QubitLike) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=qubit, axis=(0, 0, 1), angle=-math.pi / 4, phase=0)


@named_gate
def Rx(qubit: QubitLike, theta: SupportsFloat) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=qubit, axis=(1, 0, 0), angle=theta, phase=0)


@named_gate
def Ry(qubit: QubitLike, theta: SupportsFloat) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=qubit, axis=(0, 1, 0), angle=theta, phase=0)


@named_gate
def Rz(qubit: QubitLike, theta: SupportsFloat) -> BlochSphereRotation:  # noqa: N802
    return BlochSphereRotation(qubit=qubit, axis=(0, 0, 1), angle=theta, phase=0)


@named_gate
def CNOT(control: QubitLike, target: QubitLike) -> ControlledGate:  # noqa: N802
    return ControlledGate(control, X(target))


@named_gate
def CZ(control: QubitLike, target: QubitLike) -> ControlledGate:  # noqa: N802
    return ControlledGate(control, Z(target))


@named_gate
def CR(control: QubitLike, target: QubitLike, theta: SupportsFloat) -> ControlledGate:  # noqa: N802
    return ControlledGate(
        control,
        BlochSphereRotation(qubit=target, axis=(0, 0, 1), angle=theta, phase=float(theta) / 2),
    )


@named_gate
def CRk(control: QubitLike, target: QubitLike, k: SupportsInt) -> ControlledGate:  # noqa: N802
    theta = 2 * math.pi / (2 ** int(k))
    return ControlledGate(
        control, BlochSphereRotation(qubit=target, axis=(0, 0, 1), angle=theta, phase=float(theta) / 2)
    )


@named_gate
def SWAP(qubit0: QubitLike, qubit1: QubitLike) -> MatrixGate:  # noqa: N802
    return MatrixGate(
        np.array(
            [
                [1, 0, 0, 0],
                [0, 0, 1, 0],
                [0, 1, 0, 0],
                [0, 0, 0, 1],
            ],
        ),
        [qubit0, qubit1],
    )


##########################
# Non-unitary instructions
##########################


@non_unitary
def measure(qubit: QubitLike, b: BitLike) -> Measure:
    return Measure(qubit=qubit, bit=b, axis=(0, 0, 1))


@non_unitary
def init(qubit: QubitLike) -> Init:
    return Init(qubit=qubit)


@non_unitary
def reset(qubit: QubitLike) -> Reset:
    return Reset(qubit=qubit)


@non_unitary
def barrier(qubit: QubitLike) -> Barrier:
    return Barrier(qubit=qubit)


@non_unitary
def wait(qubit: QubitLike, time: SupportsInt) -> Wait:
    return Wait(qubit=qubit, time=time)


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
default_matrix_gate_set = {
    "SWAP": SWAP,
}
default_gate_alias_set = {
    "Hadamard": H,
    "Identity": I,
}

default_gate_set: Mapping[str, Callable[..., Gate]]
default_gate_set = {
    **default_bloch_sphere_rotation_set,
    **default_controlled_gate_set,
    **default_matrix_gate_set,
    **default_gate_alias_set,
}

default_unitary_set: Mapping[str, Callable[..., Unitary]]
default_unitary_set = {**default_gate_set}

default_non_unitary_set: Mapping[str, Callable[..., NonUnitary]]
default_non_unitary_set = {
    "barrier": barrier,
    "init": init,
    "measure": measure,
    "reset": reset,
    "wait": wait,
}

default_instructions: Mapping[str, Callable[..., Instruction]]
default_instructions = {
    **default_unitary_set,
    **default_non_unitary_set,
}
