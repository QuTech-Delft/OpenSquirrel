from math import atan2, cos, pi, sin, sqrt

from opensquirrel.common import ATOL, normalize_angle
from opensquirrel.decomposer.general_decomposer import Decomposer
from opensquirrel.default_gates import X90, Rz
from opensquirrel.squirrel_ir import BlochSphereRotation, Float, Gate


class McKayDecomposer(Decomposer):
    @staticmethod
    def decompose(g: Gate) -> [Gate]:
        """Return the McKay decomposition of a 1-qubit gate as a list of gates.
                gate   ---->    Rz.Rx(pi/2).Rz.Rx(pi/2).Rz

        The global phase is deemed _irrelevant_, therefore a simulator backend might produce different output
            for the input and output - the results should be equivalent modulo global phase.

        Relevant literature: https://arxiv.org/abs/1612.00858
        """
        if not isinstance(g, BlochSphereRotation):
            return [g]

        if abs(g.angle) < ATOL:
            return []

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

        decomposed_g = []

        if abs(lam) > ATOL:
            decomposed_g.append(Rz(g.qubit, Float(lam)))

        decomposed_g.append(X90(g.qubit))

        if abs(theta) > ATOL:
            decomposed_g.append(Rz(g.qubit, Float(theta)))

        decomposed_g.append(X90(g.qubit))

        if abs(phi) > ATOL:
            decomposed_g.append(Rz(g.qubit, Float(phi)))

        return decomposed_g
