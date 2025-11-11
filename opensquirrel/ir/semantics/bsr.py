from __future__ import annotations

from math import cos, floor, log10, sin
from typing import TYPE_CHECKING, Any, SupportsFloat

import numpy as np

from opensquirrel.common import ATOL, normalize_angle, repr_round
from opensquirrel.ir.expression import Axis, AxisLike, Float, Qubit, QubitLike
from opensquirrel.ir.unitary import Gate
from opensquirrel.utils.general_math import acos

if TYPE_CHECKING:
    from opensquirrel.ir import IRVisitor


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
    def arguments(self) -> tuple[Qubit | Float, ...]:
        return (self.qubit,)

    def accept(self, visitor: IRVisitor) -> Any:
        visit_gate = visitor.visit_gate(self)
        return visit_gate if visit_gate is not None else visitor.visit_bloch_sphere_rotation(self)

    def get_qubit_operands(self) -> list[Qubit]:
        return [self.qubit]

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
    def arguments(self) -> tuple[Qubit | Float, ...]:
        return (self.qubit,)

    def accept(self, visitor: IRVisitor) -> Any:
        visit_bsr = super().accept(visitor)
        return visit_bsr if visit_bsr is not None else visitor.visit_bsr_no_params(self)


class BsrFullParams(BlochSphereRotation):
    def __init__(
        self,
        qubit: QubitLike,
        axis: AxisLike,
        angle: SupportsFloat,
        phase: SupportsFloat,
        name: str = "BsrFullParams",
    ) -> None:
        BlochSphereRotation.__init__(self, qubit, axis, angle, phase, name)
        self.nx, self.ny, self.nz = (Float(component) for component in Axis(axis))
        self.theta = Float(self.angle)
        self.phi = Float(self.phase)

    @property
    def arguments(self) -> tuple[Qubit | Float, ...]:
        return self.qubit, self.nx, self.ny, self.nz, self.theta, self.phi

    def accept(self, visitor: IRVisitor) -> Any:
        visit_bsr = super().accept(visitor)
        return visit_bsr if visit_bsr is not None else visitor.visit_bsr_full_params(self)


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
    def arguments(self) -> tuple[Qubit | Float, ...]:
        return self.qubit, self.theta

    def accept(self, visitor: IRVisitor) -> Any:
        visit_bsr = super().accept(visitor)
        return visit_bsr if visit_bsr is not None else visitor.visit_bsr_angle_param(self)


class BsrUnitaryParams(BlochSphereRotation):
    def __init__(
        self,
        qubit: QubitLike,
        theta: SupportsFloat,
        phi: SupportsFloat,
        lmbda: SupportsFloat,
        name: str = "BsrUnitaryParams",
    ) -> None:
        bsr = self._get_bsr(qubit, theta, phi, lmbda)
        BlochSphereRotation.__init__(self, qubit, bsr.axis, bsr.angle, bsr.phase, name)
        self.theta = Float(theta)
        self.phi = Float(phi)
        self.lmbda = Float(lmbda)

    @property
    def arguments(self) -> tuple[Qubit | Float, ...]:
        return self.qubit, self.theta, self.phi, self.lmbda

    @staticmethod
    def _get_bsr(
        qubit: QubitLike, theta: SupportsFloat, phi: SupportsFloat, lmbda: SupportsFloat
    ) -> BlochSphereRotation:
        a = BlochSphereRotation(qubit, (0, 0, 1), lmbda, 0)
        b = BlochSphereRotation(qubit, (0, 1, 0), theta, 0)
        c = BlochSphereRotation(qubit, (0, 0, 1), phi, (float(phi) + float(lmbda)) / 2)
        return compose_bloch_sphere_rotations(compose_bloch_sphere_rotations(a, b), c)

    def accept(self, visitor: IRVisitor) -> Any:
        visit_bsr = super().accept(visitor)
        return visit_bsr if visit_bsr is not None else visitor.visit_bsr_unitary_params(self)


def compose_bloch_sphere_rotations(bsr_a: BlochSphereRotation, bsr_b: BlochSphereRotation) -> BlochSphereRotation:
    """Computes the Bloch sphere rotation resulting from the composition of two Bloch sphere rotations.
    The first rotation (A) is applied and then the second (B):

    As separate gates:
        A q
        B q

    As linear operations:
        (B * A) q

    If the final Bloch sphere rotation is anonymous, we try to match it to a default gate.

    Uses Rodrigues' rotation formula (see https://en.wikipedia.org/wiki/Rodrigues%27_rotation_formula).

    """
    if bsr_a.qubit != bsr_b.qubit:
        msg = "cannot merge two Bloch sphere rotations on different qubits"
        raise ValueError(msg)

    acos_argument = cos(bsr_a.angle / 2) * cos(bsr_b.angle / 2) - sin(bsr_a.angle / 2) * sin(bsr_b.angle / 2) * np.dot(
        bsr_a.axis, bsr_b.axis
    )
    combined_angle = 2 * acos(acos_argument)

    if abs(sin(combined_angle / 2)) < ATOL:
        return BlochSphereRotation(
            qubit=bsr_a.qubit,
            axis=(0, 0, 1),
            angle=0,
            phase=0,
        )

    order_of_magnitude = abs(floor(log10(ATOL)))
    combined_axis = np.round(
        (
            1
            / sin(combined_angle / 2)
            * (
                sin(bsr_a.angle / 2) * cos(bsr_b.angle / 2) * bsr_a.axis.value
                + cos(bsr_a.angle / 2) * sin(bsr_b.angle / 2) * bsr_b.axis.value
                + sin(bsr_a.angle / 2) * sin(bsr_b.angle / 2) * np.cross(bsr_b.axis, bsr_a.axis)
            )
        ),
        order_of_magnitude,
    )

    combined_phase = np.round(bsr_a.phase + bsr_b.phase, order_of_magnitude)

    return BlochSphereRotation.try_match_replace_with_default(
        BlochSphereRotation(
            qubit=bsr_a.qubit,
            axis=combined_axis,
            angle=combined_angle,
            phase=combined_phase,
        )
    )
