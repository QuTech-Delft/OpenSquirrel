from __future__ import annotations

import cmath
import math
from typing import TYPE_CHECKING, Any, SupportsFloat

import numpy as np
from numpy.typing import ArrayLike, DTypeLike

from opensquirrel.common import ATOL, normalize_angle, repr_round
from opensquirrel.ir.expression import Axis, AxisLike, Float
from opensquirrel.ir.ir import IRNode
from opensquirrel.ir.semantics.gate_semantic import GateSemantic

if TYPE_CHECKING:
    from opensquirrel.ir import IRVisitor
    from opensquirrel.ir.expression import Expression


def bsr_from_matrix(matrix: ArrayLike | list[list[int | DTypeLike]]) -> BlochSphereRotation:
    from opensquirrel.utils import acos

    cmatrix = np.asarray(matrix, dtype=np.complex128)
    assert cmatrix.shape == (2, 2)
    d = np.linalg.det(cmatrix)
    phase = 1 / 2 * cmath.phase(d)

    cmatrix = cmatrix / np.exp(1j * phase)
    angle = 2 * acos(1 / 2 * np.real(np.linalg.trace(cmatrix)))

    nx = (cmatrix[0, 1] + cmatrix[1, 0]) / 1j
    ny = cmatrix[1, 0] - cmatrix[0, 1]
    nz = (cmatrix[0, 0] - cmatrix[1, 1]) / 1j

    if math.sqrt(nx**2 + ny**2 + nz**2) < ATOL:
        return BlochSphereRotation(axis=(0, 0, 1), angle=0.0, phase=phase)

    if nx + ny + nz < 0:
        nx = -nx
        ny = -ny
        nz = -nz
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
    def arguments(self) -> tuple[Expression, ...]:
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
    def arguments(self) -> tuple[Expression, ...]:
        return (self.theta,)

    def accept(self, visitor: IRVisitor) -> Any:
        visit_bsr = super().accept(visitor)
        return visit_bsr if visit_bsr is not None else visitor.visit_bsr_angle_param(self)
