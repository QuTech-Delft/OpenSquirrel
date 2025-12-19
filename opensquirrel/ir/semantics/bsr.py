from __future__ import annotations

import cmath
import math
from math import cos, floor, log10, pi, sin
from typing import TYPE_CHECKING, Any, SupportsFloat

import numpy as np
from numpy.typing import ArrayLike, DTypeLike

from opensquirrel.common import ATOL, normalize_angle, repr_round
from opensquirrel.ir.expression import Axis, AxisLike, Float
from opensquirrel.ir.ir import IRNode
from opensquirrel.ir.semantics.gate_semantic import GateSemantic
from opensquirrel.utils.general_math import acos

if TYPE_CHECKING:
    from opensquirrel.ir import IRVisitor


def bsr_from_matrix(matrix: ArrayLike | list[list[int | DTypeLike]]) -> BlochSphereRotation:
    cmatrix = np.asarray(matrix, dtype=np.complex128)

    if cmatrix.shape != (2, 2):
        msg = f"Expected shape for generating BSR is (2, 2), got {cmatrix.shape}"
        raise ValueError(msg)

    a, b, c, d = map(complex, cmatrix.flatten())
    phase = cmath.phase(a * d - c * b) / 2

    a *= cmath.exp(-1j * phase)
    b *= cmath.exp(-1j * phase)
    c *= cmath.exp(-1j * phase)
    d *= cmath.exp(-1j * phase)

    angle = -2 * acos((1 / 2) * (a + d).real)
    nx = -1j * (b + c)
    ny = b - c
    nz = -1j * (a - d)

    nx, ny, nz = (x.real for x in (nx, ny, nz))

    if math.sqrt(nx**2 + ny**2 + nz**2) < ATOL:
        return BlochSphereRotation(axis=(0, 0, 1), angle=0.0, phase=phase)

    if angle <= -pi:
        angle += 2 * pi

    if nx + ny + nz < 0:
        nx = -nx
        ny = -ny
        nz = -nz
        angle = -angle
    axis = Axis((nx, ny, nz))
    return BlochSphereRotation(axis=axis, angle=angle, phase=phase)


class BlochSphereRotation(GateSemantic, IRNode):
    normalize_angle_params: bool = True

    def __init__(
        self,
        axis: AxisLike,
        angle: SupportsFloat,
        phase: SupportsFloat,
    ) -> None:
        self.axis = Axis(axis)
        self.angle = normalize_angle(angle) if self.normalize_angle_params else float(angle)
        self.phase = normalize_angle(phase) if self.normalize_angle_params else float(phase)

    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_bloch_sphere_rotation(self)

    def is_identity(self) -> bool:
        # Angle and phase are already normalized.
        return abs(self.angle) < ATOL and abs(self.phase) < ATOL

    def __repr__(self) -> str:
        return (
            f"BlochSphereRotation(axis={repr_round(self.axis)}, angle={repr_round(self.angle)}, "
            f"phase={repr_round(self.phase)})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BlochSphereRotation):
            return False

        if np.allclose(self.axis.value, other.axis.value, atol=ATOL):
            return abs(self.angle - other.angle) < ATOL and abs(self.phase - other.phase) < ATOL

        if np.allclose(self.axis.value, -other.axis.value, atol=ATOL):
            return abs(self.angle + other.angle) < ATOL and abs(self.phase + other.phase) < ATOL

        return False

    def __mul__(self, other: BlochSphereRotation) -> BlochSphereRotation:
        """Computes the single qubit gate resulting from the composition of two single
        qubit gates, by composing the Bloch sphere rotations of the two gates.
        The first rotation (A) is applied and then the second (B):

        As separate gates:
            A q
            B q

        As linear operations:
            (B * A) q

        If the final single qubit gate is anonymous, we try to match it to a default gate.

        Uses Rodrigues' rotation formula (see https://en.wikipedia.org/wiki/Rodrigues%27_rotation_formula).
        """
        acos_argument = cos(self.angle / 2) * cos(other.angle / 2) - sin(self.angle / 2) * sin(
            other.angle / 2
        ) * np.dot(self.axis, other.axis)
        combined_angle = 2 * acos(acos_argument)

        if abs(sin(combined_angle / 2)) < ATOL:
            return bsr_from_matrix([[1, 0], [0, 1]])

        order_of_magnitude = abs(floor(log10(ATOL)))
        combined_axis = np.round(
            (
                1
                / sin(combined_angle / 2)
                * (
                    sin(self.angle / 2) * cos(other.angle / 2) * self.axis.value
                    + cos(self.angle / 2) * sin(other.angle / 2) * other.axis.value
                    + sin(self.angle / 2) * sin(other.angle / 2) * np.cross(other.axis, self.axis)
                )
            ),
            order_of_magnitude,
        )

        combined_phase = np.round(self.phase + other.phase, order_of_magnitude)
        return BlochSphereRotation(
            axis=combined_axis,
            angle=combined_angle,
            phase=combined_phase,
        )


class BsrNoParams(BlochSphereRotation):
    def __init__(
        self,
        axis: AxisLike,
        angle: SupportsFloat,
        phase: SupportsFloat,
    ) -> None:
        BlochSphereRotation.__init__(self, axis, angle, phase)

    def accept(self, visitor: IRVisitor) -> Any:
        visit_bsr = super().accept(visitor)
        return visit_bsr if visit_bsr is not None else visitor.visit_bsr_no_params(self)


class BsrFullParams(BlochSphereRotation):
    def __init__(self, axis: AxisLike, angle: SupportsFloat, phase: SupportsFloat) -> None:
        BlochSphereRotation.__init__(self, axis, angle, phase)
        self.nx, self.ny, self.nz = (Float(component) for component in Axis(axis))
        self.theta = Float(self.angle)
        self.phi = Float(self.phase)

    @property
    def arguments(self) -> tuple[Float, ...]:
        return self.nx, self.ny, self.nz, self.theta, self.phi

    def accept(self, visitor: IRVisitor) -> Any:
        visit_bsr = super().accept(visitor)
        return visit_bsr if visit_bsr is not None else visitor.visit_bsr_full_params(self)


class BsrAngleParam(BlochSphereRotation):
    def __init__(
        self,
        axis: AxisLike,
        angle: SupportsFloat,
        phase: SupportsFloat,
    ) -> None:
        BlochSphereRotation.__init__(self, axis, angle, phase)
        self.theta = Float(self.angle)

    @property
    def arguments(self) -> tuple[Float, ...]:
        return (self.theta,)

    def accept(self, visitor: IRVisitor) -> Any:
        visit_bsr = super().accept(visitor)
        return visit_bsr if visit_bsr is not None else visitor.visit_bsr_angle_param(self)


class BsrUnitaryParams(BlochSphereRotation):
    def __init__(
        self,
        theta: SupportsFloat,
        phi: SupportsFloat,
        lmbda: SupportsFloat,
    ) -> None:
        bsr = self._get_bsr(theta, phi, lmbda)
        BlochSphereRotation.__init__(self, bsr.axis, bsr.angle, bsr.phase)
        self.theta = Float(theta)
        self.phi = Float(phi)
        self.lmbda = Float(lmbda)

    @property
    def arguments(self) -> tuple[Float, ...]:
        return self.theta, self.phi, self.lmbda

    @staticmethod
    def _get_bsr(theta: SupportsFloat, phi: SupportsFloat, lmbda: SupportsFloat) -> BlochSphereRotation:
        a = BlochSphereRotation((0, 0, 1), lmbda, 0)
        b = BlochSphereRotation((0, 1, 0), theta, 0)
        c = BlochSphereRotation((0, 0, 1), phi, (float(phi) + float(lmbda)) / 2)
        return a * b * c

    def accept(self, visitor: IRVisitor) -> Any:
        visit_bsr = super().accept(visitor)
        return visit_bsr if visit_bsr is not None else visitor.visit_bsr_unitary_params(self)
