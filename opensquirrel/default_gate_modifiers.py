from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, SupportsFloat

from opensquirrel.ir.semantics import BlochSphereRotation, ControlledGate
from opensquirrel.utils.context import temporary_class_attr

if TYPE_CHECKING:
    from opensquirrel.ir import QubitLike


class GateModifier:
    pass


class InverseGateModifier(GateModifier):
    def __init__(self, gate_generator: Callable[..., BlochSphereRotation]) -> None:
        self.gate_generator = gate_generator

    def __call__(self, *args: Any) -> BlochSphereRotation:
        with temporary_class_attr(BlochSphereRotation, attr="normalize_angle_params", value=False):
            gate: BlochSphereRotation = self.gate_generator(*args)
            modified_angle = gate.angle * -1
            modified_phase = gate.phase * -1
        return BlochSphereRotation.try_match_replace_with_default(
            BlochSphereRotation(qubit=gate.qubit, axis=gate.axis, angle=modified_angle, phase=modified_phase)
        )


class PowerGateModifier(GateModifier):
    def __init__(self, exponent: SupportsFloat, gate_generator: Callable[..., BlochSphereRotation]) -> None:
        self.exponent = exponent
        self.gate_generator = gate_generator

    def __call__(self, *args: Any) -> BlochSphereRotation:
        with temporary_class_attr(BlochSphereRotation, attr="normalize_angle_params", value=False):
            gate: BlochSphereRotation = self.gate_generator(*args)
            modified_angle = gate.angle * float(self.exponent)
            modified_phase = gate.phase * float(self.exponent)
        return BlochSphereRotation.try_match_replace_with_default(
            BlochSphereRotation(qubit=gate.qubit, axis=gate.axis, angle=modified_angle, phase=modified_phase)
        )


class ControlGateModifier(GateModifier):
    def __init__(self, gate_generator: Callable[..., BlochSphereRotation]) -> None:
        self.gate_generator = gate_generator

    def __call__(self, control: QubitLike, *args: Any) -> ControlledGate:
        gate: BlochSphereRotation = self.gate_generator(*args)
        return ControlledGate(control, gate)
