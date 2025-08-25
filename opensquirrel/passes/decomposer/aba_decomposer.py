"""Module containing classes that inherit from the ABADecomposer class to decompose a circuit into one of the Pauli
ABA decompositions."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, ClassVar

from opensquirrel import Rx, Ry, Rz
from opensquirrel.common import ATOL
from opensquirrel.ir import Axis, AxisLike, Gate
from opensquirrel.ir.semantics import BlochSphereRotation
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

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.index_a = self._gate_list.index(self.ra)
        self.index_b = self._gate_list.index(self.rb)

    def _find_unused_index(self) -> int:
        """Finds the index of the axis object that is not used in the decomposition.
        For example, if one selects the ZYZ decomposition, the integer returned will be 0 (since it is X).

        Returns:
            Index of the axis object that is not used in the decomposition.
        """
        return ({0, 1, 2} - {self.index_a, self.index_b}).pop()

    def _set_a_b_c_axes_values(self, axis: AxisLike) -> tuple[Any, Any, Any]:
        """Given:
        - an A-B-A decomposition strategy (where A and B can be either X, Y, or Z), and
        - a rotation axis { X: x, Y: y, Z: z } corresponding to a Bloch sphere rotation.
        Sets a new rotation axis (a, b, c) such that a = axis[A], b = axis[B], and c = axis[C].
        For example, given a Z-X-Z decomposition strategy, and an axis (x, y, z), sets (a, b, c) = (z, x, y).

        Parameters:
            axis: _normalized_ axis of a Bloch sphere rotation

         Returns:
             A triplet (a, b, c) where a, b, and c are the values of x, y, and z reordered.
        """
        axis_ = Axis(axis)
        return axis_[self.index_a], axis_[self.index_b], axis_[self._find_unused_index()]

    @staticmethod
    def _are_b_and_c_axes_in_negative_octant(b_axis_value: float, c_axis_value: float) -> bool:
        """Given an ABC axis system, and the values for axes B and C.
        Checks if the values for the B and C axes fall in one of the two negative octants (A positive or negative,
        and B and C negative, or one of them zero).

        Returns:
            True if the values for axis B and C are both negative or zero, but not zero at the same time.
            False otherwise.
        """
        return (
            (b_axis_value < 0 or abs(b_axis_value) < ATOL)
            and (c_axis_value < 0 or abs(c_axis_value) < ATOL)
            and not (abs(b_axis_value) < ATOL and abs(c_axis_value) < ATOL)
        )

    def get_decomposition_angles(self, axis: AxisLike, alpha: float) -> tuple[float, float, float]:
        """Given:
        - an A-B-A decomposition strategy (where A and B can be either X, Y, or Z), and
        - the rotation axis and angle corresponding to a Bloch sphere rotation.
        Calculates the rotation angles around axes A, B, and C,
        such that the original Bloch sphere rotation can be expressed as U = Ra(theta3) Rb(theta2) Rc(theta1),
        Rn meaning rotation around axis N

        Parameters:
            axis: _normalized_ axis of a Bloch sphere rotation
            alpha: angle of a Bloch sphere rotation

        Returns:
            A triplet (theta_1, theta_2, theta_3), where theta_1, theta_2, and theta_3 are the rotation angles around
            axes A, B, and C, respectively.
        """
        if not (-math.pi + ATOL < alpha <= math.pi + ATOL):
            msg = "angle needs to be normalized"
            raise ValueError(msg)

        a_axis_value, b_axis_value, c_axis_value = self._set_a_b_c_axes_values(axis)

        # Calculate primary angle
        p = 2 * math.atan2(a_axis_value * math.sin(alpha / 2), math.cos(alpha / 2))

        # Calculate theta 2
        theta_2 = 2 * acos(math.cos(alpha / 2) * math.sqrt(1 + (a_axis_value * math.tan(alpha / 2)) ** 2))
        theta_2 = math.copysign(theta_2, alpha)

        # Calculate secondary angle
        if abs(math.sin(theta_2 / 2)) < ATOL:
            # This can be anything, but setting m = p means theta_3 == 0, which is better for gate count.
            m = p
        else:
            m = 2 * acos(float(b_axis_value) * math.sin(alpha / 2) / math.sin(theta_2 / 2))
            if math.pi - abs(m) > ATOL:
                ret_sign = 2 * math.atan2(c_axis_value, a_axis_value)
                m = math.copysign(m, ret_sign)

        # Check if the sign of the secondary angle has to be flipped
        if are_axes_consecutive(self.index_a, self.index_b):
            m = -m

        # Calculate theta 1 and theta 2
        theta_1 = (p + m) / 2
        theta_3 = p - theta_1

        # Check if theta 1 and theta 3 have to be swapped
        if ABADecomposer._are_b_and_c_axes_in_negative_octant(b_axis_value, c_axis_value):
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

        theta1, theta2, theta3 = self.get_decomposition_angles(g.axis, g.angle)
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
