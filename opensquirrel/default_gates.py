import math

from opensquirrel.squirrel_ir import *


@named_gate
def h(q: Qubit) -> Gate:
    return BlochSphereRotation(qubit=q, axis=(1, 0, 1), angle=math.pi, phase=math.pi / 2)


@named_gate
def x(q: Qubit) -> Gate:
    return BlochSphereRotation(qubit=q, axis=(1, 0, 0), angle=math.pi, phase=math.pi / 2)


@named_gate
def x90(q: Qubit) -> Gate:
    return BlochSphereRotation(qubit=q, axis=(1, 0, 0), angle=math.pi / 2, phase=0)


@named_gate
def y(q: Qubit) -> Gate:
    return BlochSphereRotation(qubit=q, axis=(0, 1, 0), angle=math.pi, phase=math.pi / 2)


@named_gate
def y90(q: Qubit) -> Gate:
    return BlochSphereRotation(qubit=q, axis=(0, 1, 0), angle=math.pi / 2, phase=0)


@named_gate
def z(q: Qubit) -> Gate:
    return BlochSphereRotation(qubit=q, axis=(0, 0, 1), angle=math.pi, phase=math.pi / 2)


@named_gate
def z90(q: Qubit) -> Gate:
    return BlochSphereRotation(qubit=q, axis=(0, 0, 1), angle=math.pi / 2, phase=0)


@named_gate
def rx(q: Qubit, theta: Float) -> Gate:
    return BlochSphereRotation(qubit=q, axis=(1, 0, 0), angle=theta.value, phase=0)


@named_gate
def ry(q: Qubit, theta: Float) -> Gate:
    return BlochSphereRotation(qubit=q, axis=(0, 1, 0), angle=theta.value, phase=0)


@named_gate
def rz(q: Qubit, theta: Float) -> Gate:
    return BlochSphereRotation(qubit=q, axis=(0, 0, 1), angle=theta.value, phase=0)


@named_gate
def cnot(control: Qubit, target: Qubit) -> Gate:
    return ControlledGate(control, x(target))


@named_gate
def cz(control: Qubit, target: Qubit) -> Gate:
    return ControlledGate(control, z(target))


@named_gate
def cr(control: Qubit, target: Qubit, theta: Float) -> Gate:
    return ControlledGate(
        control, BlochSphereRotation(qubit=target, axis=(0, 0, 1), angle=theta.value, phase=theta.value / 2)
    )


@named_gate
def crk(control: Qubit, target: Qubit, k: Int) -> Gate:
    theta = 2 * math.pi / (2**k.value)
    return ControlledGate(control, BlochSphereRotation(qubit=target, axis=(0, 0, 1), angle=theta, phase=theta / 2))


default_gate_set = [h, x, x90, y, y90, z, z90, cz, cr, crk, cnot, rx, ry, rz, x]
default_gate_aliases = {"X": x, "RX": rx, "RY": ry, "RZ": rz, "Hadamard": h, "H": h}
