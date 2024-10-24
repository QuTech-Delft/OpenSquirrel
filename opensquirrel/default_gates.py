from __future__ import annotations

import math
from typing import Any

from opensquirrel.ir import BlochSphereRotation, ControlledGate, Float, Gate, Int, QubitLike, named_gate


class NamedGateFunctor:
    def __init__(self, parameter: Any = None):
        self.parameter = parameter

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        pass


@named_gate
class I(NamedGateFunctor):
    def __init__(self, parameter: Any = None):
        super().__init__(parameter)

    def __call__(self, q: QubitLike) -> BlochSphereRotation:  # noqa: E743
        return BlochSphereRotation.identity(q)


@named_gate
class H(NamedGateFunctor):
    def __init__(self, parameter: Any = None):
        super().__init__(parameter)

    def __call__(self, q: QubitLike) -> BlochSphereRotation:
        return BlochSphereRotation(qubit=q, axis=(1, 0, 1), angle=math.pi, phase=math.pi / 2)


@named_gate
class X(NamedGateFunctor):
    def __init__(self, parameter: Any = None):
        super().__init__(parameter)

    def __call__(self, q: QubitLike) -> BlochSphereRotation:
        return BlochSphereRotation(qubit=q, axis=(1, 0, 0), angle=math.pi, phase=math.pi / 2)


@named_gate
class X90(NamedGateFunctor):
    def __init__(self, parameter: Any = None):
        super().__init__(parameter)

    def __call__(self, q: QubitLike) -> BlochSphereRotation:
        return BlochSphereRotation(qubit=q, axis=(1, 0, 0), angle=math.pi / 2, phase=0)


@named_gate
class mX90(NamedGateFunctor):
    def __init__(self, parameter: Any = None):
        super().__init__(parameter)

    def __call__(self, q: QubitLike) -> BlochSphereRotation:
        return BlochSphereRotation(qubit=q, axis=(1, 0, 0), angle=-math.pi / 2, phase=-0)


@named_gate
class Y(NamedGateFunctor):
    def __init__(self, parameter: Any = None):
        super().__init__(parameter)

    def __call__(self, q: QubitLike) -> BlochSphereRotation:
        return BlochSphereRotation(qubit=q, axis=(0, 1, 0), angle=math.pi, phase=math.pi / 2)


@named_gate
class Y90(NamedGateFunctor):
    def __init__(self, parameter: Any = None):
        super().__init__(parameter)

    def __call__(self, q: QubitLike) -> BlochSphereRotation:
        return BlochSphereRotation(qubit=q, axis=(0, 1, 0), angle=math.pi / 2, phase=0)


@named_gate
class mY90(NamedGateFunctor):
    def __init__(self, parameter: Any = None):
        super().__init__(parameter)

    def __call__(self, q: QubitLike) -> BlochSphereRotation:
        return BlochSphereRotation(qubit=q, axis=(0, 1, 0), angle=-math.pi / 2, phase=0)


@named_gate
class Z(NamedGateFunctor):
    def __init__(self, parameter: Any = None):
        super().__init__(parameter)

    def __call__(self, q: QubitLike) -> BlochSphereRotation:
        return BlochSphereRotation(qubit=q, axis=(0, 0, 1), angle=math.pi, phase=math.pi / 2)


@named_gate
class S(NamedGateFunctor):
    def __init__(self, parameter: Any = None):
        super().__init__(parameter)

    def __call__(self, q: QubitLike) -> BlochSphereRotation:
        return BlochSphereRotation(qubit=q, axis=(0, 0, 1), angle=math.pi / 2, phase=0)


@named_gate
class Sdag:
    def __init__(self, parameter: Any = None):
        pass

    def __call__(self, q: QubitLike) -> BlochSphereRotation:
        return BlochSphereRotation(qubit=q, axis=(0, 0, 1), angle=-math.pi / 2, phase=0)


@named_gate
class T(NamedGateFunctor):
    def __init__(self, parameter: Any = None):
        super().__init__(parameter)

    def __call__(self, q: QubitLike) -> BlochSphereRotation:
        return BlochSphereRotation(qubit=q, axis=(0, 0, 1), angle=math.pi / 4, phase=0)


@named_gate
class Tdag(NamedGateFunctor):
    def __init__(self, parameter: Any = None):
        super().__init__(parameter)

    def __call__(self, q: QubitLike) -> BlochSphereRotation:
        return BlochSphereRotation(qubit=q, axis=(0, 0, 1), angle=-math.pi / 4, phase=0)


@named_gate
class Rx(NamedGateFunctor):
    def __init__(self, parameter: Any = None):
        super().__init__(parameter)

    def __call__(self, q: QubitLike) -> BlochSphereRotation:
        self.theta = Float(self.parameter).value
        return BlochSphereRotation(qubit=q, axis=(1, 0, 0), angle=self.theta, phase=0)


@named_gate
class Ry(NamedGateFunctor):
    def __init__(self, parameter: Any = None):
        super().__init__(parameter)

    def __call__(self, q: QubitLike) -> BlochSphereRotation:
        self.theta = Float(self.parameter).value
        return BlochSphereRotation(qubit=q, axis=(0, 1, 0), angle=self.theta, phase=0)


@named_gate
class Rz(NamedGateFunctor):
    def __init__(self, parameter: Any = None):
        super().__init__(parameter)

    def __call__(self, q: QubitLike) -> BlochSphereRotation:
        self.theta = Float(self.parameter).value
        return BlochSphereRotation(qubit=q, axis=(0, 0, 1), angle=self.theta, phase=0)


@named_gate
class CNOT(NamedGateFunctor):
    def __init__(self, parameter: Any = None):
        super().__init__(parameter)

    def __call__(self, control: QubitLike, target: QubitLike) -> ControlledGate:
        return ControlledGate(control, X()(target))


@named_gate
class CZ(NamedGateFunctor):
    def __init__(self, parameter: Any = None):
        super().__init__(parameter)

    def __call__(self, control: QubitLike, target: QubitLike) -> ControlledGate:
        return ControlledGate(control, Z()(target))


@named_gate
class CR(NamedGateFunctor):
    def __init__(self, parameter: Any = None):
        super().__init__(parameter)

    def __call__(self, control: QubitLike, target: QubitLike) -> ControlledGate:
        self.theta = Float(self.parameter).value
        return ControlledGate(
            control,
            BlochSphereRotation(qubit=target, axis=(0, 0, 1), angle=self.theta, phase=self.theta / 2),
        )


@named_gate
class CRk(NamedGateFunctor):
    def __init__(self, parameter: Any = None):
        super().__init__(parameter)

    def __call__(self, control: QubitLike, target: QubitLike) -> ControlledGate:
        self.theta = 2 * math.pi / (2 ** Int(self.parameter).value)
        return ControlledGate(
            control,
            BlochSphereRotation(qubit=target, axis=(0, 0, 1), angle=self.theta, phase=self.theta / 2)
        )


default_bloch_sphere_rotations_without_params: list[type[NamedGateFunctor]]
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
default_bloch_sphere_rotations: list[type[NamedGateFunctor]]
default_bloch_sphere_rotations = [
    *default_bloch_sphere_rotations_without_params,
    Rx,
    Ry,
    Rz,
]
default_gate_set: list[type[NamedGateFunctor]]
default_gate_set = [
    *default_bloch_sphere_rotations,
    CNOT,
    CZ,
    CR,
    CRk,
]

default_gate_aliases: dict[str, type[NamedGateFunctor]]
default_gate_aliases = {
    "Hadamard": H,
    "Identity": I,
}
