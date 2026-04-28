from __future__ import annotations

from math import atan2, cos, pi, sin, sqrt

from opensquirrel import X90, I, Rz
from opensquirrel.common import ATOL, normalize_angle
from opensquirrel.ir import Axis, Gate
from opensquirrel.ir.single_qubit_gate import SingleQubitGate
from opensquirrel.passes.decomposer import ZXZDecomposer
from opensquirrel.passes.decomposer.general_decomposer import Decomposer


class McKayDecomposer(Decomposer):
    def decompose(self, instruction: Gate) -> list[Gate]:
        """Decomposes a single-qubit gate using the McKay decomposition into a sequence of (at most)
        5 single-qubit gates; according tot the pattern Rz-Rx(pi/2)-Rz-Rx(pi/2)-Rz, where the angles
        of the Rz gates are to be determined.

        Note:
            The global phase of the original gate is (in general) not preserved in this decomposition.

        The decomposition is based on the procedure described in
        [McKay et al. (2016)](https://arxiv.org/abs/1612.00858).

        Args:
            gate (Gate): Single-qubit gate to decompose.

        Returns:
            A sequence of (at most) 5 single-qubit gates that decompose the original gate.

        """
        if not isinstance(instruction, SingleQubitGate) or instruction == X90(instruction.qubit):
            return [instruction]

        gate = instruction

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
