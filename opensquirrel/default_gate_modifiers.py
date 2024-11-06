from __future__ import annotations

from abc import ABC
from collections.abc import Callable
from opensquirrel.ir import BlochSphereRotation, ControlledGate, QubitLike
from typing import SupportsInt, Any


class GateModifier(ABC):
    pass


class InverseGateModifier(GateModifier):
    def __init__(self, generator_f_gate: Callable[..., BlochSphereRotation]):
        self.generator_f_gate = generator_f_gate

    def __call__(self, *args: Any) -> BlochSphereRotation:
        gate: BlochSphereRotation = self.generator_f_gate(*args)
        modified_angle = gate.angle * -1
        return BlochSphereRotation(qubit=gate.qubit, axis=gate.axis, angle=modified_angle, phase=gate.phase)


class PowerGateModifier(GateModifier):
    def __init__(self, exponent: SupportsInt, generator_f_gate: Callable[..., BlochSphereRotation]):
        self.exponent = exponent
        self.generator_f_gate = generator_f_gate

    def __call__(self, *args: Any) -> BlochSphereRotation:
        gate: BlochSphereRotation = self.generator_f_gate(*args)
        modified_angle = gate.angle * self.exponent
        return BlochSphereRotation(qubit=gate.qubit, axis=gate.axis, angle=modified_angle, phase=gate.phase)


class ControlGateModifier(GateModifier):
    def __init__(self, generator_f_gate: Callable[..., BlochSphereRotation]):
        self.generator_f_gate = generator_f_gate

    def __call__(self, control: QubitLike, *args: Any) -> ControlledGate:
        gate: BlochSphereRotation = self.generator_f_gate(*args)
        return ControlledGate(control, gate)
