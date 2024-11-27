"""Module containing classes that inherit from the ABADecomposer class to decompose a circuit into one of the Pauli
ABA decompositions."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, ClassVar

from opensquirrel.common import ATOL
from opensquirrel.default_instructions import Rx, Ry, Rz
from opensquirrel.ir import Axis, AxisLike, BlochSphereRotation, Gate
from opensquirrel.passes.decomposer.general_decomposer import Decomposer
from opensquirrel.utils import acos, are_axes_consecutive, filter_out_identities


class ABADecomposer(Decomposer, ABC):
    @property
    @abstractmethod
    def ra(self) -> Callable[..., BlochSphereRotation]: ...

    @property
    @abstractmethod
    def rb(self) -> Callable[..., BlochSphereRotation]: ...

    _gate_list: ClassVar[list[Callable[..., BlochSphereRotation]]] = [Rx, Ry, Rz]

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
            A triple (theta1, theta2, theta3) corresponding to the decomposition of the arbitrary Bloch sphere rotation
            into U = Ra(theta3) Rb(theta2) Ra(theta1)
        """

        def _set_axes_values() -> tuple[Any, Any, Any]:
            """Given a decomposition strategy and an input axis.
            For example:
            - a Z-X-Z decomposition, which sets ra=Z and rb=X, and thus
              index_a = 2 (index of Z in [Rx, Ry, Rz]), index_b = 0, and index_c = 1 (unused). And
            - an axis (x, y, z).

             Returns:
                 A tuple (a, b, c) where a = axis(index_a), b = axis(index_b), and c = axis(index_c).
                 For the example above, a = z, b = x, and c = y.
            """
            _axis = Axis(axis)
            return _axis[self.index_a], _axis[self.index_b], _axis[self._find_unused_index()]

        def _calculate_primary_angle() -> float:
            return 2 * math.atan2(a_axis_value * math.sin(alpha / 2), math.cos(alpha / 2))

        def _calculate_secondary_angle() -> float:
            if abs(math.sin(theta_2 / 2)) < ATOL:
                # This can be anything, but setting m = p means theta_3 == 0, which is better for gate count.
                return p
            ret: float = 2 * acos(float(b_axis_value) * math.sin(alpha / 2) / math.sin(theta_2 / 2))
            if math.pi - abs(ret) > ATOL:
                ret_sign = 2 * math.atan2(c_axis_value, a_axis_value)
                ret = math.copysign(ret, ret_sign)
            return ret

        def _calculate_theta_2() -> float:
            ret = 2 * acos(math.cos(alpha / 2) * math.sqrt(1 + (a_axis_value * math.tan(alpha / 2)) ** 2))
            return math.copysign(ret, alpha)

        if not (-math.pi + ATOL < alpha <= math.pi + ATOL):
            msg = "angle needs to be normalized"
            raise ValueError(msg)

        a_axis_value, b_axis_value, c_axis_value = _set_axes_values()
        p = _calculate_primary_angle()
        theta_2 = _calculate_theta_2()
        m = _calculate_secondary_angle()

        # Check if the sign of the secondary angle has to be flipped
        if are_axes_consecutive(self.index_a, self.index_b):
            m = -m

        theta_1 = (p + m) / 2
        theta_3 = p - theta_1

        # Check if theta 1 and theta 3 have to be swapped
        if b_axis_value < 0 and c_axis_value < 0:
            theta_1, theta_3 = theta_3, theta_1

        return theta_1, theta_2, theta_3

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
        a1 = self.ra(g.qubit, theta1)
        b = self.rb(g.qubit, theta2)
        a2 = self.ra(g.qubit, theta3)
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
