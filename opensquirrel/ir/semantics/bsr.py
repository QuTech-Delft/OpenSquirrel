from __future__ import annotations

from typing import TYPE_CHECKING, Any, SupportsFloat

import numpy as np

from opensquirrel.common import ATOL, normalize_angle, repr_round
from opensquirrel.ir import AxisLike, Bit, Float, Gate, Qubit, QubitLike
from opensquirrel.ir.expression import BaseAxis

from numpy.typing import NDArray

from opensquirrel.ir import IRVisitor

if TYPE_CHECKING:
    from opensquirrel.ir.expression import Expression

class Axis(BaseAxis):
    """The ``Axis`` object parses and stores a vector containing 3 elements.

    The input vector is always normalized before it is stored.
    """

    @staticmethod
    def parse(axis: AxisLike) -> NDArray[np.float64]:
        """Parse and validate an ``AxisLike``.

        Check if the `axis` can be cast to a 1DArray of length 3, raise an error otherwise.
        After casting to an array, the axis is normalized.

        Args:
            axis: ``AxisLike`` to validate and parse.

        Returns:
            Parsed axis represented as a 1DArray of length 3.
        """
        if isinstance(axis, Axis):
            return axis.value

        try:
            axis = np.asarray(axis, dtype=float)
        except (ValueError, TypeError) as e:
            msg = "axis requires an ArrayLike"
            raise TypeError(msg) from e
        axis = axis.flatten()
        if len(axis) != 3:
            msg = f"axis requires an ArrayLike of length 3, but received an ArrayLike of length {len(axis)}"
            raise ValueError(msg)
        if np.all(axis == 0):
            msg = "axis requires at least one element to be non-zero"
            raise ValueError(msg)
        axis = axis / np.linalg.norm(axis)
        return axis 
    
    def accept(self, visitor: IRVisitor) -> Any:
        """Accept the ``Axis``."""
        return visitor.visit_axis(self)


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
