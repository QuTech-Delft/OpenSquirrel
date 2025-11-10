from __future__ import annotations

from math import pi
from typing import SupportsFloat, Any

import numpy as np

from opensquirrel.ir import Axis, AxisLike, QubitLike
from opensquirrel.ir.semantics import BlochSphereRotation, BsrAngleParam, BsrFullParams, BsrNoParams
from opensquirrel.ir.semantics.bsr import BlochSphereRotation
from opensquirrel.ir.single_qubit_gate import SingleQubitGate
from opensquirrel.ir.expression import Float


def try_match_replace_with_default_gate(gate: SingleQubitGate) -> SingleQubitGate:
    """Try replacing a given BlochSphereRotation with a default BlochSphereRotation.
        It does that by matching the input BlochSphereRotation to a default BlochSphereRotation.

    Returns:
            A default BlockSphereRotation if this BlochSphereRotation is close to it,
            or the input BlochSphereRotation otherwise.
    """
    from opensquirrel.default_instructions import (
        default_bsr_set_without_rn,
        default_bsr_with_angle_param_set,
    )

    for gate_name in default_bsr_set_without_rn:
        arguments: tuple[Any, ...] = (gate.qubit,)
        if gate_name in default_bsr_with_angle_param_set:
            arguments += (Float(gate.bsr.angle),)
        gate = default_bsr_set_without_rn[gate_name](*arguments)
        gate_bsr = BlochSphereRotation(gate.qubit, axis=gate.bsr.axis, angle=gate.bsr.angle, phase=gate.bsr.phase)
        if gate.bsr == gate_bsr:
            return gate
    
    nx, ny, nz = gate.bsr.axis.value
    return Rn(gate.qubit, nx=nx, ny=ny, nz=nz, theta=gate.bsr.angle, phi=gate.bsr.phase)

class Rn(SingleQubitGate):
    def __init__(
        self,
        qubit: QubitLike,
        nx: SupportsFloat,
        ny: SupportsFloat,
        nz: SupportsFloat,
        theta: SupportsFloat,
        phi: SupportsFloat,
    ) -> None:
        super().__init__(qubit=qubit)
        axis: AxisLike = Axis(np.asarray([nx, ny, nz], dtype=np.float64))
        self.bsr: BlochSphereRotation = BsrFullParams(qubit=qubit, axis=axis, angle=theta, phase=phi)


class Rx(SingleQubitGate):
    def __init__(self, qubit: QubitLike, theta: SupportsFloat) -> None:
        super().__init__(qubit=qubit)
        self.bsr = BsrAngleParam(qubit=qubit, axis=(1, 0, 0), angle=theta, phase=0.0)


class Ry(SingleQubitGate):
    def __init__(self, qubit: QubitLike, theta: SupportsFloat) -> None:
        super().__init__(qubit=qubit)
        self.bsr = BsrAngleParam(qubit=qubit, axis=(0, 1, 0), angle=theta, phase=0.0)


class Rz(SingleQubitGate):
    def __init__(self, qubit: QubitLike, theta: SupportsFloat) -> None:
        super().__init__(qubit=qubit)
        self.bsr = BsrAngleParam(qubit=qubit, axis=(0, 0, 1), angle=theta, phase=0.0)


class I(SingleQubitGate):  # noqa: E742
    def __init__(self, qubit: QubitLike) -> None:
        super().__init__(qubit=qubit)
        self.bsr = BsrNoParams(qubit=qubit, axis=(0, 0, 1), angle=0, phase=0)


class H(SingleQubitGate):
    def __init__(self, qubit: QubitLike) -> None:
        super().__init__(qubit=qubit)
        self.bsr = BsrNoParams(qubit=qubit, axis=(1, 0, 1), angle=pi, phase=pi / 2)


class X(SingleQubitGate):
    def __init__(self, qubit: QubitLike) -> None:
        super().__init__(qubit=qubit)
        self.bsr = BsrNoParams(qubit=qubit, axis=(1, 0, 0), angle=pi, phase=pi / 2)


class X90(SingleQubitGate):
    def __init__(self, qubit: QubitLike) -> None:
        super().__init__(qubit=qubit)
        self.bsr = BsrNoParams(qubit=qubit, axis=(1, 0, 0), angle=pi / 2, phase=pi / 4)


class MinusX90(SingleQubitGate):
    def __init__(self, qubit: QubitLike) -> None:
        super().__init__(qubit=qubit)
        self.bsr = BsrNoParams(qubit=qubit, axis=(1, 0, 0), angle=-pi / 2, phase=-pi / 4)


class Y(SingleQubitGate):
    def __init__(self, qubit: QubitLike) -> None:
        super().__init__(qubit=qubit)
        self.bsr = BsrNoParams(qubit=qubit, axis=(0, 1, 0), angle=pi, phase=pi / 2)


class Y90(SingleQubitGate):
    def __init__(self, qubit: QubitLike) -> None:
        super().__init__(qubit=qubit)
        self.bsr = BsrNoParams(qubit=qubit, axis=(0, 1, 0), angle=pi / 2, phase=pi / 4)


class MinusY90(SingleQubitGate):
    def __init__(self, qubit: QubitLike) -> None:
        super().__init__(qubit=qubit)
        self.bsr = BsrNoParams(qubit=qubit, axis=(0, 1, 0), angle=-pi / 2, phase=-pi / 4)


class Z(SingleQubitGate):
    def __init__(self, qubit: QubitLike) -> None:
        super().__init__(qubit=qubit)
        self.bsr = BsrNoParams(qubit=qubit, axis=(0, 0, 1), angle=pi, phase=pi / 2)


class S(SingleQubitGate):
    def __init__(self, qubit: QubitLike) -> None:
        super().__init__(qubit=qubit)
        self.bsr = BsrNoParams(qubit=qubit, axis=(0, 0, 1), angle=pi / 2, phase=pi / 4)


class SDagger(SingleQubitGate):
    def __init__(self, qubit: QubitLike) -> None:
        super().__init__(qubit=qubit)
        self.bsr = BsrNoParams(qubit=qubit, axis=(0, 0, 1), angle=-pi / 2, phase=-pi / 4)


class T(SingleQubitGate):
    def __init__(self, qubit: QubitLike) -> None:
        super().__init__(qubit=qubit)
        self.bsr = BsrNoParams(qubit=qubit, axis=(0, 0, 1), angle=pi / 4, phase=pi / 8)


class TDagger(SingleQubitGate):
    def __init__(self, qubit: QubitLike) -> None:
        super().__init__(qubit=qubit)
        self.bsr = BsrNoParams(qubit=qubit, axis=(0, 0, 1), angle=-pi / 4, phase=-pi / 8)
