from __future__ import annotations

import math
from collections.abc import Iterable

from opensquirrel.common import ATOL
from opensquirrel.decomposer.general_decomposer import Decomposer
from opensquirrel.default_gates import Ry, Rz
from opensquirrel.ir import BlochSphereRotation, Float, Gate
from opensquirrel.utils.identity_filter import filter_out_identities


def get_zyz_decomposition_angles(alpha: float, axis: Iterable[float]) -> tuple[float, float, float]:
    """
    Gives the angles used in the Z-Y-Z decomposition of the Bloch sphere rotation
    characterized by a rotation around `axis` of angle `alpha`.

    Parameters:
        alpha: angle of the Bloch sphere rotation
        axis: _normalized_ axis of the Bloch sphere rotation

    Returns:
        A triple (theta1, theta2, theta3) corresponding to the decomposition of the
        arbitrary Bloch sphere rotation into U = Rz(theta3) Ry(theta2) Rz(theta1)

    """
    nx, ny, nz = axis

    assert abs(nx**2 + ny**2 + nz**2 - 1) < ATOL, "Axis needs to be normalized"

    assert -math.pi + ATOL < alpha <= math.pi + ATOL, "Angle needs to be normalized"

    if abs(alpha - math.pi) < ATOL:
        # alpha == pi, math.tan(alpha / 2) is not defined.

        p: float
        if abs(nz) < ATOL:
            theta2 = math.pi
            p = 0
            m = 2 * math.acos(ny)

        else:
            p = math.pi
            theta2 = 2 * math.acos(nz)

            if abs(nz - 1) < ATOL or abs(nz + 1) < ATOL:
                m = p  # This can be anything, but setting m = p means theta3 == 0, which is better for gate count.
            else:
                m = 2 * math.acos(ny / math.sqrt(1 - nz**2))

    else:
        p = 2 * math.atan2(nz * math.sin(alpha / 2), math.cos(alpha / 2))

        acos_argument = math.cos(alpha / 2) * math.sqrt(1 + (nz * math.tan(alpha / 2)) ** 2)

        # This fixes float approximations like 1.0000000000002 which acos doesn't like.
        acos_argument = max(min(acos_argument, 1.0), -1.0)

        theta2 = 2 * math.acos(acos_argument)
        theta2 = math.copysign(theta2, alpha)

        if abs(math.sin(theta2 / 2)) < ATOL:
            m = p  # This can be anything, but setting m = p means theta3 == 0, which is better for gate count.
        else:
            acos_argument = ny * math.sin(alpha / 2) / math.sin(theta2 / 2)

            # This fixes float approximations like 1.0000000000002 which acos doesn't like.
            acos_argument = max(min(acos_argument, 1.0), -1.0)

            m = 2 * math.acos(acos_argument)

    theta1 = (p + m) / 2

    theta3 = p - theta1

    return theta1, theta2, theta3


class ZYZDecomposer(Decomposer):
    def decompose(self, g: Gate) -> list[Gate]:
        if not isinstance(g, BlochSphereRotation):
            # Only decomposer single-qubit gates.
            return [g]

        theta1, theta2, theta3 = get_zyz_decomposition_angles(g.angle, g.axis)

        z1 = Rz(g.qubit, Float(theta1))
        y = Ry(g.qubit, Float(theta2))
        z2 = Rz(g.qubit, Float(theta3))

        # Note: written like this, the decomposition doesn't preserve the global phase, which is fine
        # since the global phase is a physically irrelevant artifact of the mathematical
        # model we use to describe the quantum system.

        # Should we want to preserve it, we would need to use a raw BlochSphereRotation, which would then
        # be an anonymous gate in the resulting decomposed circuit:
        # z2 = BlochSphereRotation(qubit=g.qubit, angle=theta3, axis=(0, 0, 1), phase = g.phase)

        return filter_out_identities([z1, y, z2])
