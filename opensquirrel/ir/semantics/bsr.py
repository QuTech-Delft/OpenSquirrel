from __future__ import annotations

from typing import TYPE_CHECKING, Any, SupportsFloat

import numpy as np

from opensquirrel.common import ATOL, normalize_angle, repr_round
from opensquirrel.ir.expression import Axis, AxisLike, Float
from opensquirrel.ir.ir import IRNode
from opensquirrel.ir.semantics.gate_semantic import GateSemantic

if TYPE_CHECKING:
    from opensquirrel.ir import IRVisitor
    from opensquirrel.ir.expression import Expression


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
