from __future__ import annotations

from typing import TYPE_CHECKING, Any, SupportsFloat

import numpy as np

from opensquirrel.common import ATOL, normalize_angle, repr_round
from opensquirrel.ir import Axis, AxisLike, Bit, Float, Gate, Qubit, QubitLike

if TYPE_CHECKING:
    from opensquirrel.ir import IRVisitor
    from opensquirrel.ir.expression import Expression


class BlochSphereRotation(Gate):
    normalize_angle_params: bool = True

    def __init__(
        self,
        qubit: QubitLike,
        axis: AxisLike,
        angle: SupportsFloat,
        phase: SupportsFloat,
        name: str = "BlochSphereRotation",
    ) -> None:
        Gate.__init__(self, name)
        self.qubit = Qubit(qubit)
        self.axis = Axis(axis)
        self.angle = normalize_angle(angle) if self.normalize_angle_params else float(angle)
        self.phase = normalize_angle(phase) if self.normalize_angle_params else float(phase)

    @staticmethod
    def try_match_replace_with_default(bsr: BlochSphereRotation) -> BlochSphereRotation:
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
        from opensquirrel.ir.default_gates import Rn

        for gate_name in default_bsr_set_without_rn:
            arguments: tuple[Any, ...] = (bsr.qubit,)
            if gate_name in default_bsr_with_angle_param_set:
                arguments += (Float(bsr.angle),)
            gate = default_bsr_set_without_rn[gate_name](*arguments)
            gate_bsr = BlochSphereRotation(gate.qubit, axis=gate.axis, angle=gate.angle, phase=gate.phase)
            if bsr == gate_bsr:
                return gate
        nx, ny, nz = (Float(component) for component in bsr.axis)
        return Rn(bsr.qubit, nx, ny, nz, Float(bsr.angle), Float(bsr.phase))

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return (self.qubit,)

    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_bloch_sphere_rotation(self)

    def get_qubit_operands(self) -> list[Qubit]:
        return [self.qubit]

    def get_bit_operands(self) -> list[Bit]:
        return []

    def is_identity(self) -> bool:
        # Angle and phase are already normalized.
        return abs(self.angle) < ATOL and abs(self.phase) < ATOL

    def __repr__(self) -> str:
        return (
            f"{self.name}(qubit={self.qubit}, axis={repr_round(self.axis)}, angle={repr_round(self.angle)}, "
            f"phase={repr_round(self.phase)})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BlochSphereRotation):
            return False

        if self.qubit != other.qubit:
            return False

        if np.allclose(self.axis.value, other.axis.value, atol=ATOL):
            return abs(self.angle - other.angle) < ATOL and abs(self.phase - other.phase) < ATOL

        if np.allclose(self.axis.value, -other.axis.value, atol=ATOL):
            return abs(self.angle + other.angle) < ATOL and abs(self.phase + other.phase) < ATOL

        return False


class BsrNoParams(BlochSphereRotation):
    def __init__(
        self,
        qubit: QubitLike,
        axis: AxisLike,
        angle: SupportsFloat,
        phase: SupportsFloat,
        name: str = "BsrNoParams",
    ) -> None:
        BlochSphereRotation.__init__(self, qubit, axis, angle, phase, name)

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return (self.qubit,)

    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_bsr_no_params(self)


class BsrFullParams(BlochSphereRotation):
    def __init__(
        self, qubit: QubitLike, axis: AxisLike, angle: SupportsFloat, phase: SupportsFloat, name: str = "BsrFullParams"
    ) -> None:
        BlochSphereRotation.__init__(self, qubit, axis, angle, phase, name)
        self.nx, self.ny, self.nz = (Float(component) for component in Axis(axis))
        self.theta = Float(self.angle)
        self.phi = Float(self.phase)

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return self.qubit, self.nx, self.ny, self.nz, self.theta, self.phi

    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_bsr_full_params(self)


class BsrAngleParam(BlochSphereRotation):
    def __init__(
        self,
        qubit: QubitLike,
        axis: AxisLike,
        angle: SupportsFloat,
        phase: SupportsFloat,
        name: str = "BsrNoParams",
    ) -> None:
        BlochSphereRotation.__init__(self, qubit, axis, angle, phase, name)
        self.theta = Float(self.angle)

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return self.qubit, self.theta

    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_bsr_angle_param(self)
