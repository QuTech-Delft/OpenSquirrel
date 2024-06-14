from __future__ import annotations

import math
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable

import numpy as np

from opensquirrel.common import ATOL
from opensquirrel.decomposer.general_decomposer import Decomposer
from opensquirrel.default_gates import Rx, Ry, Rz
from opensquirrel.ir import Axis, AxisLike, BlochSphereRotation, Float, Gate, Qubit
from opensquirrel.utils.identity_filter import filter_out_identities


class ABADecomposer(Decomposer, ABC):
    @property
    @abstractmethod
    def ra(self) -> Callable[..., BlochSphereRotation]: ...

    @property
    @abstractmethod
    def rb(self) -> Callable[..., BlochSphereRotation]: ...

    _gate_list: list[str] = [Rx.__name__, Ry.__name__, Rz.__name__]

    def __init__(self) -> None:
        self.index_a = self._gate_list.index(self.ra.__dict__["__wrapped__"].__name__)
        self.index_b = self._gate_list.index(self.rb.__dict__["__wrapped__"].__name__)

    def get_decomposition_angles(self, alpha: float, axis: AxisLike) -> tuple[float, float, float]:
        """
        Gives the angles used in the A-B-A decomposition of the Bloch sphere rotation
        characterized by a rotation around `axis` of angle `alpha`.

        Parameters:
            alpha: angle of the Bloch sphere rotation
            axis: _normalized_ axis of the Bloch sphere rotation

        Returns:
            A triple (theta1, theta2, theta3) corresponding to the decomposition of the
            arbitrary Bloch sphere rotation into U = Ra(theta3) Rb(theta2) Ra(theta1)

        """
        axis = Axis(axis)

        if not (-math.pi + ATOL < alpha <= math.pi + ATOL):
            ValueError("Angle needs to be normalized")

        if abs(alpha - math.pi) < ATOL:
            # alpha == pi, math.tan(alpha / 2) is not defined.

            p: float
            if abs(axis[self.index_a]) < ATOL:
                theta2 = math.pi
                p = 0
                m = 2 * math.acos(axis[self.index_b])

            else:
                p = math.pi
                theta2 = 2 * math.acos(axis[self.index_a])

                if abs(axis[self.index_a] - 1) < ATOL or abs(axis[self.index_a] + 1) < ATOL:
                    m = p  # This can be anything, but setting m = p means theta3 == 0, which is better for gate count.
                else:
                    m = 2 * math.acos(axis[self.index_b] / math.sqrt(1 - axis[self.index_a] ** 2))

        else:
            p = 2 * math.atan2(axis[self.index_a] * math.sin(alpha / 2), math.cos(alpha / 2))

            acos_argument = math.cos(alpha / 2) * math.sqrt(1 + (axis[self.index_a] * math.tan(alpha / 2)) ** 2)

            # This fixes float approximations like 1.0000000000002 which acos doesn't like.
            acos_argument = max(min(acos_argument, 1.0), -1.0)

            theta2 = 2 * math.acos(acos_argument)
            theta2 = math.copysign(theta2, alpha)

            if abs(math.sin(theta2 / 2)) < ATOL:
                m = p  # This can be anything, but setting m = p means theta3 == 0, which is better for gate count.
            else:
                acos_argument = axis[self.index_b] * math.sin(alpha / 2) / math.sin(theta2 / 2)

                # This fixes float approximations like 1.0000000000002 which acos doesn't like.
                acos_argument = max(min(acos_argument, 1.0), -1.0)

                m = 2 * math.acos(acos_argument)

        theta1 = (p + m) / 2

        theta3 = p - theta1
        return theta1, theta2, theta3

    def decompose(self, g: Gate) -> list[Gate]:
        if not isinstance(g, BlochSphereRotation):
            # Only decomposer single-qubit gates.
            return [g]

        theta1, theta2, theta3 = self.get_decomposition_angles(g.angle, g.axis)
        a1 = self.ra.__dict__["__wrapped__"](g.qubit, Float(theta1))
        b = self.rb.__dict__["__wrapped__"](g.qubit, Float(theta2))
        a2 = self.ra.__dict__["__wrapped__"](g.qubit, Float(theta3))

        # Note: written like this, the decomposition doesn't preserve the global phase, which is fine
        # since the global phase is a physically irrelevant artifact of the mathematical
        # model we use to describe the quantum system.

        # Should we want to preserve it, we would need to use a raw BlochSphereRotation, which would then
        # be an anonymous gate in the resulting decomposed circuit:
        # z2 = BlochSphereRotation(qubit=g.qubit, angle=theta3, axis=(0, 0, 1), phase = g.phase)

        return filter_out_identities([a1, b, a2])


class ZYZDecomposer(ABADecomposer):
    ra = Rz
    rb = Ry


class XYXDecomposer(ABADecomposer):
    ra = Rx
    rb = Ry


class YZYDecomposer(ABADecomposer):
    ra = Ry
    rb = Rz


class XZXDecomposer(ABADecomposer):
    ra = Rx
    rb = Rz


class YXYDecomposer(ABADecomposer):
    ra = Ry
    rb = Rx


class ZXZDecomposer(ABADecomposer):
    ra = Rz
    rb = Rx
