from __future__ import annotations

from math import atan2, cos, pi, sin, sqrt

from opensquirrel.common import ATOL, normalize_angle
from opensquirrel.decomposer.aba_decomposer import ZXZDecomposer
from opensquirrel.decomposer.general_decomposer import Decomposer
from opensquirrel.default_gates import X90, Rz
from opensquirrel.ir import BlochSphereRotation, Float, Gate


class McKayDecomposer(Decomposer):
    def decompose(self, g: Gate) -> list[Gate]:
        """Return the McKay decomposition of a 1-qubit gate as a list of gates.
                gate   ---->    Rz.Rx(pi/2).Rz.Rx(pi/2).Rz

        The global phase is deemed _irrelevant_, therefore a simulator backend might produce different output.
        The results should be equivalent modulo global phase.
        Notice that, if the gate is Rz or X90, it will not be decomposed further, since they are natively used
        in the McKay decomposition.

        Relevant literature: https://arxiv.org/abs/1612.00858
        """
        if not isinstance(g, BlochSphereRotation) or g.name == "Rz" or g.name == "X90":
            return [g]

        if abs(g.angle) < ATOL:
            return []

        if g.axis[0] == 0 and g.axis[1] == 0:
            rz_angle = float(g.angle * g.axis[2])
            return [Rz(g.qubit, Float(rz_angle))]

        zxz_decomposition = ZXZDecomposer().decompose(g)
        zxz_angle = 0.0
        if len(zxz_decomposition) >= 2 and isinstance(zxz_decomposition[1], BlochSphereRotation):
            zxz_angle = zxz_decomposition[1].angle

        if abs(zxz_angle - pi / 2) < ATOL:
            zxz_decomposition[1] = X90(g.qubit)
            return zxz_decomposition

        # McKay decomposition
        za_mod = sqrt(cos(g.angle / 2) ** 2 + (g.axis[2] * sin(g.angle / 2)) ** 2)
        zb_mod = abs(sin(g.angle / 2)) * sqrt(g.axis[0] ** 2 + g.axis[1] ** 2)

        theta = pi - 2 * atan2(zb_mod, za_mod)

        alpha = atan2(-sin(g.angle / 2) * g.axis[2], cos(g.angle / 2))
        beta = atan2(-sin(g.angle / 2) * g.axis[0], -sin(g.angle / 2) * g.axis[1])

        lam = beta - alpha
        phi = -beta - alpha - pi

        lam = normalize_angle(lam)
        phi = normalize_angle(phi)
        theta = normalize_angle(theta)

        decomposed_g: list[Gate] = []

        if abs(theta) < ATOL and lam == phi:
            decomposed_g.append(X90(g.qubit))
            decomposed_g.append(X90(g.qubit))
            return decomposed_g

        if abs(lam) > ATOL:
            decomposed_g.append(Rz(g.qubit, Float(lam)))

        decomposed_g.append(X90(g.qubit))

        if abs(theta) > ATOL:
            decomposed_g.append(Rz(g.qubit, Float(theta)))

        decomposed_g.append(X90(g.qubit))

        if abs(phi) > ATOL:
            decomposed_g.append(Rz(g.qubit, Float(phi)))

        return decomposed_g
