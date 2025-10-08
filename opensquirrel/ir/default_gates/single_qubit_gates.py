from math import pi
from typing import SupportsFloat

import numpy as np

from opensquirrel.ir import Axis, AxisLike, QubitLike
from opensquirrel.ir.semantics import BsrAngleParam, BsrFullParams, BsrNoParams


class Rn(BsrFullParams):
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
        BsrFullParams.__init__(self, qubit=qubit, axis=axis, angle=theta, phase=phi, name="Rn")


class Rx(BsrAngleParam):
    def __init__(self, qubit: QubitLike, theta: SupportsFloat) -> None:
        BsrAngleParam.__init__(self, qubit=qubit, axis=(1, 0, 0), angle=theta, phase=0.0, name="Rx")


class Ry(BsrAngleParam):
    def __init__(self, qubit: QubitLike, theta: SupportsFloat) -> None:
        BsrAngleParam.__init__(self, qubit=qubit, axis=(0, 1, 0), angle=theta, phase=0.0, name="Ry")


class Rz(BsrAngleParam):
    def __init__(self, qubit: QubitLike, theta: SupportsFloat) -> None:
        BsrAngleParam.__init__(self, qubit=qubit, axis=(0, 0, 1), angle=theta, phase=0.0, name="Rz")


class I(BsrNoParams):  # noqa: E742
    def __init__(self, qubit: QubitLike) -> None:
        BsrNoParams.__init__(self, qubit=qubit, axis=(0, 0, 1), angle=0, phase=0, name="I")


class H(BsrNoParams):
    def __init__(self, qubit: QubitLike) -> None:
        BsrNoParams.__init__(self, qubit=qubit, axis=(1, 0, 1), angle=pi, phase=pi / 2, name="H")


class X(BsrNoParams):
    def __init__(self, qubit: QubitLike) -> None:
        BsrNoParams.__init__(self, qubit=qubit, axis=(1, 0, 0), angle=pi, phase=pi / 2, name="X")


class X90(BsrNoParams):
    def __init__(self, qubit: QubitLike) -> None:
        BsrNoParams.__init__(self, qubit=qubit, axis=(1, 0, 0), angle=pi / 2, phase=pi / 4, name="X90")


class MinusX90(BsrNoParams):
    def __init__(self, qubit: QubitLike) -> None:
        BsrNoParams.__init__(self, qubit=qubit, axis=(1, 0, 0), angle=-pi / 2, phase=-pi / 4, name="mX90")


class Y(BsrNoParams):
    def __init__(self, qubit: QubitLike) -> None:
        BsrNoParams.__init__(self, qubit=qubit, axis=(0, 1, 0), angle=pi, phase=pi / 2, name="Y")


class Y90(BsrNoParams):
    def __init__(self, qubit: QubitLike) -> None:
        BsrNoParams.__init__(self, qubit=qubit, axis=(0, 1, 0), angle=pi / 2, phase=pi / 4, name="Y90")


class MinusY90(BsrNoParams):
    def __init__(self, qubit: QubitLike) -> None:
        BsrNoParams.__init__(self, qubit=qubit, axis=(0, 1, 0), angle=-pi / 2, phase=-pi / 4, name="mY90")


class Z(BsrNoParams):
    def __init__(self, qubit: QubitLike) -> None:
        BsrNoParams.__init__(self, qubit=qubit, axis=(0, 0, 1), angle=pi, phase=pi / 2, name="Z")


class S(BsrNoParams):
    def __init__(self, qubit: QubitLike) -> None:
        BsrNoParams.__init__(self, qubit=qubit, axis=(0, 0, 1), angle=pi / 2, phase=pi / 4, name="S")


class SDagger(BsrNoParams):
    def __init__(self, qubit: QubitLike) -> None:
        BsrNoParams.__init__(self, qubit=qubit, axis=(0, 0, 1), angle=-pi / 2, phase=-pi / 4, name="Sdag")


class T(BsrNoParams):
    def __init__(self, qubit: QubitLike) -> None:
        BsrNoParams.__init__(self, qubit=qubit, axis=(0, 0, 1), angle=pi / 4, phase=pi / 8, name="T")


class TDagger(BsrNoParams):
    def __init__(self, qubit: QubitLike) -> None:
        BsrNoParams.__init__(self, qubit=qubit, axis=(0, 0, 1), angle=-pi / 4, phase=-pi / 8, name="Tdag")
