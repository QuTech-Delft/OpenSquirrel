from __future__ import annotations

from collections.abc import Callable
from opensquirrel.ir import BlochSphereRotation, ControlledGate, Gate, QubitLike, gate_modifier
from typing import SupportsInt


@gate_modifier
def inv(
    generator_f_gate: Callable[..., BlochSphereRotation],
    q: QubitLike
) -> BlochSphereRotation:
    gate: BlochSphereRotation = generator_f_gate(q)
    modified_angle = gate.angle * -1
    return BlochSphereRotation(qubit=gate.qubit, axis=gate.axis, angle=modified_angle, phase=gate.phase)


@gate_modifier
def pow(
    generator_f_gate: Callable[..., BlochSphereRotation],
    exponent: SupportsInt,
    q: QubitLike
) -> BlochSphereRotation:
    gate: BlochSphereRotation = generator_f_gate(q)
    modified_angle = gate.angle * exponent
    return BlochSphereRotation(qubit=gate.qubit, axis=gate.axis, angle=modified_angle, phase=gate.phase)


@gate_modifier
def ctrl(
    generator_f_gate: Callable[..., BlochSphereRotation],
    control: QubitLike,
    target: QubitLike
) -> ControlledGate:
    gate: BlochSphereRotation = generator_f_gate(target)
    return ControlledGate(control, gate)


default_gate_modifier_set: list[Callable[..., Gate]]
default_gate_modifier_set = [inv, pow, ctrl]
