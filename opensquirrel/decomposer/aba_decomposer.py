"""Module containing classes that inherit from the ABADecomposer class to decompose a circuit into one of the Pauli
ABA decompositions."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from collections.abc import Callable

import numpy as np

from opensquirrel.common import ATOL
from opensquirrel.decomposer.general_decomposer import Decomposer
from opensquirrel.default_gates import Rx, Ry, Rz
from opensquirrel.ir import Axis, AxisLike, BlochSphereRotation, Float, Gate
from opensquirrel.utils.identity_filter import filter_out_identities


class ABADecomposer(Decomposer, ABC):
    @property
    @abstractmethod
    def ra(self) -> Callable[..., BlochSphereRotation]: ...

    @property
    @abstractmethod
    def rb(self) -> Callable[..., BlochSphereRotation]: ...

    _gate_list: list[Callable[..., BlochSphereRotation]] = [Rx, Ry, Rz]

    def __init__(self) -> None:
        self.index_a = self._gate_list.index(self.ra)
        self.index_b = self._gate_list.index(self.rb)

    def _find_unused_index(self) -> int:
        """Finds the index of the axis object that is not used in the decomposition.
        For example, if one selects the ZYZ decomposition, the integer returned will be 0 (since it is X).
        Returns:
            Index of the axis object that is not used in the decomposition.
        """
        return ({0, 1, 2} - {self.index_a, self.index_b}).pop()

    def get_decomposition_angles(self, alpha: float, axis: AxisLike) -> tuple[float, float, float]:
        """Gives the angles used in the A-B-A decomposition of the Bloch sphere rotation
        characterized by a rotation around `axis` of angle `alpha`.

        Parameters:
            alpha: angle of the Bloch sphere rotation
            axis: _normalized_ axis of the Bloch sphere rotation

        Returns:
            A triple (theta1, theta2, theta3) corresponding to the decomposition of the
            arbitrary Bloch sphere rotation into U = Ra(theta3) Rb(theta2) Ra(theta1)

        """
        axis = Axis(axis)
        a_axis_value = axis[self.index_a]
        b_axis_value = axis[self.index_b]
        c_axis_value = axis[self._find_unused_index()]

        if not (-math.pi + ATOL < alpha <= math.pi + ATOL):
            raise ValueError("angle needs to be normalized")

        if abs(alpha - math.pi) < ATOL:
            # alpha == pi, math.tan(alpha / 2) is not defined.
            if abs(a_axis_value) < ATOL:
                theta2 = math.pi
                p = 0.0
                m = 2 * math.acos(b_axis_value)
            else:
                p = math.pi
                theta2 = 2 * math.acos(a_axis_value)
                if abs(a_axis_value - 1) < ATOL or abs(a_axis_value + 1) < ATOL:
                    m = p  # This can be anything, but setting m = p means theta3 == 0, which is better for gate count.
                else:
                    m = 2 * math.acos(
                        round(b_axis_value / math.sqrt(1 - a_axis_value**2), abs(math.floor(math.log10(ATOL))))
                    )

        else:
            p = 2 * math.atan2(a_axis_value * math.sin(alpha / 2), math.cos(alpha / 2))
            acos_argument = math.cos(alpha / 2) * math.sqrt(1 + (a_axis_value * math.tan(alpha / 2)) ** 2)

            # This fixes float approximations like 1.0000000000002, which acos does not like.
            acos_argument = max(min(acos_argument, 1.0), -1.0)

            theta2 = 2 * math.acos(acos_argument)
            theta2 = math.copysign(theta2, alpha)

            if abs(math.sin(theta2 / 2)) < ATOL:
                m = p  # This can be anything, but setting m = p means theta3 == 0, which is better for gate count.
            else:
                acos_argument = float(b_axis_value) * math.sin(alpha / 2) / math.sin(theta2 / 2)

                # This fixes float approximations like 1.0000000000002, which acos does not like.
                acos_argument = max(min(acos_argument, 1.0), -1.0)
                m = 2 * math.acos(acos_argument)
                if math.pi - abs(m) > ATOL:
                    m_sign = 2 * math.atan(c_axis_value / a_axis_value)
                    m = math.copysign(m, m_sign)

        is_sin_m_negative = self.index_a - self.index_b in (-1, 2)
        if is_sin_m_negative:
            m = m * -1

        theta1 = (p + m) / 2
        theta3 = p - theta1

        return theta1, theta2, theta3

    def decompose(self, g: Gate) -> list[Gate]:
        """General A-B-A decomposition function for a single gate.

        Args:
            g: gate to decompose.

        Returns:
            Three gates, following the A-B-A convention, corresponding to the decomposition of the input gate.
        """
        if not isinstance(g, BlochSphereRotation):
            # We only decompose Bloch sphere rotations.
            return [g]

        theta1, theta2, theta3 = self.get_decomposition_angles(g.angle, g.axis)
        a1 = self.ra(g.qubit, Float(theta1))
        b = self.rb(g.qubit, Float(theta2))
        a2 = self.ra(g.qubit, Float(theta3))
        return filter_out_identities([a1, b, a2])


class XYXDecomposer(ABADecomposer):
    """Class responsible for the X-Y-X decomposition."""

    @property
    def ra(self) -> Callable[..., BlochSphereRotation]:
        return Rx

    @property
    def rb(self) -> Callable[..., BlochSphereRotation]:
        return Ry


class XZXDecomposer(ABADecomposer):
    """Class responsible for the X-Z-X decomposition."""

    @property
    def ra(self) -> Callable[..., BlochSphereRotation]:
        return Rx

    @property
    def rb(self) -> Callable[..., BlochSphereRotation]:
        return Rz


class YXYDecomposer(ABADecomposer):
    """Class responsible for the Y-X-Y decomposition."""

    @property
    def ra(self) -> Callable[..., BlochSphereRotation]:
        return Ry

    @property
    def rb(self) -> Callable[..., BlochSphereRotation]:
        return Rx


class YZYDecomposer(ABADecomposer):
    """Class responsible for the Y-Z-Y decomposition."""

    @property
    def ra(self) -> Callable[..., BlochSphereRotation]:
        return Ry

    @property
    def rb(self) -> Callable[..., BlochSphereRotation]:
        return Rz


class ZXZDecomposer(ABADecomposer):
    """Class responsible for the Z-X-Z decomposition."""

    @property
    def ra(self) -> Callable[..., BlochSphereRotation]:
        return Rz

    @property
    def rb(self) -> Callable[..., BlochSphereRotation]:
        return Rx


class ZYZDecomposer(ABADecomposer):
    """Class responsible for the Z-Y-Z decomposition."""

    @property
    def ra(self) -> Callable[..., BlochSphereRotation]:
        return Rz

    @property
    def rb(self) -> Callable[..., BlochSphereRotation]:
        return Ry
