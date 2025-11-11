from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, SupportsFloat

from opensquirrel.ir.default_gates.single_qubit_gates import try_match_replace_with_default_gate
from opensquirrel.ir.semantics import ControlledGate
from opensquirrel.ir.semantics.bsr import BlochSphereRotation
from opensquirrel.ir.single_qubit_gate import SingleQubitGate
from opensquirrel.utils.context import temporary_class_attr

if TYPE_CHECKING:
    from opensquirrel.ir import QubitLike


class GateModifier:
    pass


class InverseGateModifier(GateModifier):
    def __init__(self, gate_generator: Callable[..., SingleQubitGate]) -> None:
        self.gate_generator = gate_generator

    def __call__(self, *args: Any) -> SingleQubitGate:
        with temporary_class_attr(BlochSphereRotation, attr="normalize_angle_params", value=False):
            gate: SingleQubitGate = self.gate_generator(*args)
            modified_angle = gate.bsr.angle * -1
            modified_phase = gate.bsr.phase * -1
        gate = SingleQubitGate.from_bsr(
            gate.qubit, BlochSphereRotation(axis=gate.bsr.axis, angle=modified_angle, phase=modified_phase)
        )
        return try_match_replace_with_default_gate(gate)


class PowerGateModifier(GateModifier):
    def __init__(self, exponent: SupportsFloat, gate_generator: Callable[..., SingleQubitGate]) -> None:
        self.exponent = exponent
        self.gate_generator = gate_generator

    def __call__(self, *args: Any) -> SingleQubitGate:
        with temporary_class_attr(BlochSphereRotation, attr="normalize_angle_params", value=False):
            gate: SingleQubitGate = self.gate_generator(*args)
            modified_angle = gate.bsr.angle * float(self.exponent)
            modified_phase = gate.bsr.phase * float(self.exponent)
        gate = SingleQubitGate.from_bsr(
            gate.qubit, BlochSphereRotation(axis=gate.bsr.axis, angle=modified_angle, phase=modified_phase)
        )
        return try_match_replace_with_default_gate(gate)


class ControlGateModifier(GateModifier):
    def __init__(self, gate_generator: Callable[..., SingleQubitGate]) -> None:
        self.gate_generator = gate_generator

    def __call__(self, control: QubitLike, *args: Any) -> ControlledGate:
        gate: SingleQubitGate = self.gate_generator(*args)
        return ControlledGate(control, gate)
