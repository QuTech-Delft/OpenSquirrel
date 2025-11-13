from __future__ import annotations

from math import pi
from typing import SupportsFloat

import numpy as np

from opensquirrel.ir import Axis, AxisLike, QubitLike
from opensquirrel.ir.semantics import BsrAngleParam, BsrFullParams, BsrNoParams
from opensquirrel.ir.single_qubit_gate import SingleQubitGate


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
        axis: AxisLike = Axis(np.asarray([nx, ny, nz], dtype=np.float64))
        super().__init__(qubit=qubit, gate_semantic=BsrFullParams(axis=axis, angle=theta, phase=phi), name="Rn")


class Rx(SingleQubitGate):
    def __init__(self, qubit: QubitLike, theta: SupportsFloat) -> None:
        super().__init__(qubit=qubit, gate_semantic=BsrAngleParam(axis=(1, 0, 0), angle=theta, phase=0.0), name="Rx")


class Ry(SingleQubitGate):
    def __init__(self, qubit: QubitLike, theta: SupportsFloat) -> None:
        super().__init__(qubit=qubit, gate_semantic=BsrAngleParam(axis=(0, 1, 0), angle=theta, phase=0.0), name="Ry")


class Rz(SingleQubitGate):
    def __init__(self, qubit: QubitLike, theta: SupportsFloat) -> None:
        super().__init__(qubit=qubit, gate_semantic=BsrAngleParam(axis=(0, 0, 1), angle=theta, phase=0.0), name="Rz")


class I(SingleQubitGate):  # noqa: E742
    def __init__(self, qubit: QubitLike) -> None:
        super().__init__(qubit=qubit, gate_semantic=BsrNoParams(axis=(0, 0, 1), angle=0, phase=0), name="I")


class H(SingleQubitGate):
    def __init__(self, qubit: QubitLike) -> None:
        super().__init__(qubit=qubit, gate_semantic=BsrNoParams(axis=(1, 0, 1), angle=pi, phase=pi / 2), name="H")


class X(SingleQubitGate):
    def __init__(self, qubit: QubitLike) -> None:
        super().__init__(qubit=qubit, gate_semantic=BsrNoParams(axis=(1, 0, 0), angle=pi, phase=pi / 2), name="X")


class X90(SingleQubitGate):
    def __init__(self, qubit: QubitLike) -> None:
        super().__init__(qubit=qubit, gate_semantic=BsrNoParams(axis=(1, 0, 0), angle=pi / 2, phase=pi / 4), name="X90")


class MinusX90(SingleQubitGate):
    def __init__(self, qubit: QubitLike) -> None:
        super().__init__(
            qubit=qubit, gate_semantic=BsrNoParams(axis=(1, 0, 0), angle=-pi / 2, phase=-pi / 4), name="mX90"
        )


class Y(SingleQubitGate):
    def __init__(self, qubit: QubitLike) -> None:
        super().__init__(qubit=qubit, gate_semantic=BsrNoParams(axis=(0, 1, 0), angle=pi, phase=pi / 2), name="Y")


class Y90(SingleQubitGate):
    def __init__(self, qubit: QubitLike) -> None:
        super().__init__(qubit=qubit, gate_semantic=BsrNoParams(axis=(0, 1, 0), angle=pi / 2, phase=pi / 4), name="Y90")


class MinusY90(SingleQubitGate):
    def __init__(self, qubit: QubitLike) -> None:
        super().__init__(
            qubit=qubit, gate_semantic=BsrNoParams(axis=(0, 1, 0), angle=-pi / 2, phase=-pi / 4), name="mY90"
        )


class Z(SingleQubitGate):
    def __init__(self, qubit: QubitLike) -> None:
        super().__init__(qubit=qubit, gate_semantic=BsrNoParams(axis=(0, 0, 1), angle=pi, phase=pi / 2), name="Z")


class S(SingleQubitGate):
    def __init__(self, qubit: QubitLike) -> None:
        super().__init__(qubit=qubit, gate_semantic=BsrNoParams(axis=(0, 0, 1), angle=pi / 2, phase=pi / 4), name="S")


class SDagger(SingleQubitGate):
    def __init__(self, qubit: QubitLike) -> None:
        super().__init__(
            qubit=qubit, gate_semantic=BsrNoParams(axis=(0, 0, 1), angle=-pi / 2, phase=-pi / 4), name="Sdag"
        )


class T(SingleQubitGate):
    def __init__(self, qubit: QubitLike) -> None:
        super().__init__(qubit=qubit, gate_semantic=BsrNoParams(axis=(0, 0, 1), angle=pi / 4, phase=pi / 8), name="T")


class TDagger(SingleQubitGate):
    def __init__(self, qubit: QubitLike) -> None:
        super().__init__(
            qubit=qubit, gate_semantic=BsrNoParams(axis=(0, 0, 1), angle=-pi / 4, phase=-pi / 8), name="Tdag"
        )
