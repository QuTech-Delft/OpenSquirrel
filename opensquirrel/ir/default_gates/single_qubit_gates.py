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

class Z90(BsrNoParams):
    def __init__(self, qubit: QubitLike) -> None:
        BsrNoParams.__init__(self, qubit=qubit, axis=(0, 0, 1), angle=pi / 2, phase=pi / 4, name="Z90")

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


class U(BsrFullParams):
    def __init__(
        self,
        qubit: QubitLike,
        theta: SupportsFloat,
        phi: SupportsFloat,
        lmbda: SupportsFloat,
    ) -> None:
        from opensquirrel.passes.merger.general_merger import compose_bloch_sphere_rotations # noqa # lazy import 
        a= Rn(qubit, 0, 0, 1, lmbda, phi=0)
        b= Rn(qubit, 0, 1, 0, theta, phi=0)
        c= Rn(qubit, 0, 0, 1, phi, phi=(phi+lmbda)/2)        
        bsr = compose_bloch_sphere_rotations(compose_bloch_sphere_rotations(a, b), c)
        
        BsrFullParams.__init__(self, qubit=qubit, axis=bsr.axis, angle=bsr.angle, phase=bsr.phase, name="U")


if __name__=='__main__':
    lmbda=.1
    theta=.2
    phi=.3
    qubit=0
    u=U(qubit, lmbda,theta, phi)
    print(u)
        