from __future__ import annotations

from math import atan2, cos, pi, sin, sqrt

from opensquirrel import X90, I, Rz
from opensquirrel.common import ATOL, normalize_angle
from opensquirrel.ir import Axis, Gate
from opensquirrel.ir.single_qubit_gate import SingleQubitGate
from opensquirrel.passes.decomposer import ZXZDecomposer
from opensquirrel.passes.decomposer.general_decomposer import Decomposer


class McKayDecomposer(Decomposer):
    def decompose(self, gate: Gate) -> list[Gate]:
        """Return the McKay decomposition of a 1-qubit gate as a list of gates.
                gate   ---->    Rz.Rx(pi/2).Rz.Rx(pi/2).Rz

        The global phase is deemed _irrelevant_, therefore a simulator backend might produce different output.
        The results should be equivalent modulo global phase.
        Notice that, if the gate is Rz or X90, it will not be decomposed further, since they are natively used
        in the McKay decomposition.

        Relevant literature: https://arxiv.org/abs/1612.00858
        """
        if not isinstance(gate, SingleQubitGate) or gate == X90(gate.qubit):
            return [gate]

        if abs(gate.bsr.angle) < ATOL:
            return [I(gate.qubit)]

        if gate.bsr.axis[0] == 0 and gate.bsr.axis[1] == 0:
            rz_angle = float(gate.bsr.angle * gate.bsr.axis[2])
            return [Rz(gate.qubit, rz_angle)]

        zxz_decomposition = ZXZDecomposer().decompose(gate)
        zxz_angle = 0.0
        if len(zxz_decomposition) >= 2:
            zxz_angle = next(
                gate.bsr.angle
                for gate in zxz_decomposition
                if isinstance(gate, SingleQubitGate) and gate.bsr.axis == Axis(1, 0, 0)
            )

        if abs(zxz_angle - pi / 2) < ATOL:
            return [
                X90(gate.qubit) if isinstance(gate, SingleQubitGate) and gate.bsr.axis == Axis(1, 0, 0) else gate
                for gate in zxz_decomposition
            ]

        # McKay decomposition
        za_mod = sqrt(cos(gate.bsr.angle / 2) ** 2 + (gate.bsr.axis[2] * sin(gate.bsr.angle / 2)) ** 2)
        zb_mod = abs(sin(gate.bsr.angle / 2)) * sqrt(gate.bsr.axis[0] ** 2 + gate.bsr.axis[1] ** 2)

        theta = pi - 2 * atan2(zb_mod, za_mod)

        alpha = atan2(-sin(gate.bsr.angle / 2) * gate.bsr.axis[2], cos(gate.bsr.angle / 2))
        beta = atan2(-sin(gate.bsr.angle / 2) * gate.bsr.axis[0], -sin(gate.bsr.angle / 2) * gate.bsr.axis[1])

        lam = beta - alpha
        phi = -beta - alpha - pi

        lam = normalize_angle(lam)
        phi = normalize_angle(phi)
        theta = normalize_angle(theta)

        decomposed_g: list[Gate] = []

        if abs(theta) < ATOL and lam == phi:
            decomposed_g.extend((X90(gate.qubit), X90(gate.qubit)))
            return decomposed_g

        if abs(lam) > ATOL:
            decomposed_g.append(Rz(gate.qubit, lam))
        decomposed_g.append(X90(gate.qubit))

        if abs(theta) > ATOL:
            decomposed_g.append(Rz(gate.qubit, theta))

        decomposed_g.append(X90(gate.qubit))

        if abs(phi) > ATOL:
            decomposed_g.append(Rz(gate.qubit, phi))

        return decomposed_g
