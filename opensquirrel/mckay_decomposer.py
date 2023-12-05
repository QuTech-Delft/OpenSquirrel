from math import acos, atan2, cos, pi, sin, sqrt
from typing import Tuple

import numpy as np

from opensquirrel.common import ATOL, normalize_angle
from opensquirrel.default_gates import rz, x90
from opensquirrel.squirrel_ir import BlochSphereRotation, Float, Gate, Qubit, SquirrelIR


class _McKayDecomposerImpl:
    def __init__(self, number_of_qubits: int, qubit_register_name: str):
        self.output = SquirrelIR(number_of_qubits=number_of_qubits, qubit_register_name=qubit_register_name)
        self.accumulated_1q_gates = {}

    def decompose_and_add(self, qubit: Qubit, angle: float, axis: Tuple[float, float, float]):
        if abs(angle) < ATOL:
            return

        # McKay decomposition

        za_mod = sqrt(cos(angle / 2) ** 2 + (axis[2] * sin(angle / 2)) ** 2)
        zb_mod = abs(sin(angle / 2)) * sqrt(axis[0] ** 2 + axis[1] ** 2)

        theta = pi - 2 * atan2(zb_mod, za_mod)

        alpha = atan2(-sin(angle / 2) * axis[2], cos(angle / 2))
        beta = atan2(-sin(angle / 2) * axis[0], -sin(angle / 2) * axis[1])

        lam = beta - alpha
        phi = -beta - alpha - pi

        lam = normalize_angle(lam)
        phi = normalize_angle(phi)
        theta = normalize_angle(theta)

        if abs(lam) > ATOL:
            self.output.add_gate(rz(qubit, Float(lam)))

        self.output.add_gate(x90(qubit))

        if abs(theta) > ATOL:
            self.output.add_gate(rz(qubit, Float(theta)))

        self.output.add_gate(x90(qubit))

        if abs(phi) > ATOL:
            self.output.add_gate(rz(qubit, Float(phi)))

    def flush(self, q):
        if q not in self.accumulated_1q_gates:
            return
        p = self.accumulated_1q_gates.pop(q)
        self.decompose_and_add(q, p["angle"], p["axis"])

    def flush_all(self):
        while len(self.accumulated_1q_gates) > 0:
            self.flush(next(iter(self.accumulated_1q_gates)))

    def accumulate(self, qubit, bloch_sphere_rotation: BlochSphereRotation):
        axis, angle, phase = bloch_sphere_rotation.axis, bloch_sphere_rotation.angle, bloch_sphere_rotation.phase

        if qubit not in self.accumulated_1q_gates:
            self.accumulated_1q_gates[qubit] = {"angle": angle, "axis": axis, "phase": phase}
            return

        existing = self.accumulated_1q_gates[qubit]
        combined_phase = phase + existing["phase"]

        a = angle
        l = axis
        b = existing["angle"]
        m = existing["axis"]

        combined_angle = 2 * acos(cos(a / 2) * cos(b / 2) - sin(a / 2) * sin(b / 2) * np.dot(l, m))

        if abs(sin(combined_angle / 2)) < ATOL:
            self.accumulated_1q_gates.pop(qubit)
            return

        combined_axis = (
            1
            / sin(combined_angle / 2)
            * (sin(a / 2) * cos(b / 2) * l + cos(a / 2) * sin(b / 2) * m + sin(a / 2) * sin(b / 2) * np.cross(l, m))
        )

        self.accumulated_1q_gates[qubit] = {"angle": combined_angle, "axis": combined_axis, "phase": combined_phase}

    def process_gate(self, gate: Gate):
        qubit_arguments = [arg for arg in gate.arguments if isinstance(arg, Qubit)]

        if len(qubit_arguments) >= 2:
            [self.flush(q) for q in qubit_arguments]
            self.output.add_gate(gate)
            return

        if len(qubit_arguments) == 0:
            assert False, "Unsupported"
            return

        assert isinstance(gate, BlochSphereRotation), f"Not supported for single qubit gate `{gate.name}`: {type(gate)}"

        self.accumulate(qubit_arguments[0], gate)


def decompose_mckay(squirrel_ir):
    impl = _McKayDecomposerImpl(squirrel_ir.number_of_qubits, squirrel_ir.qubit_register_name)

    for statement in squirrel_ir.statements:
        if not isinstance(statement, Gate):
            continue

        impl.process_gate(statement)

    impl.flush_all()

    return impl.output  # FIXME: instead of returning a new IR, modify existing one
