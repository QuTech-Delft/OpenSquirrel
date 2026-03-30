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
from opensquirrel.ir.single_qubit_gate import SingleQubitGate
from opensquirrel.passes.decomposer.general_decomposer import Decomposer
from opensquirrel.utils.general_math import acos, are_axes_consecutive
from opensquirrel.utils.identity_filter import filter_out_identities


class ABADecomposer(Decomposer, ABC):
    _gate_list: ClassVar[list[Callable[..., SingleQubitGate]]] = [Rx, Ry, Rz]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.index_a = self._gate_list.index(self.Ra)
        self.index_b = self._gate_list.index(self.Rb)

    @property
    @abstractmethod
    def Ra(self) -> Callable[..., SingleQubitGate]: ...  # noqa: N802

    @property
    @abstractmethod
    def Rb(self) -> Callable[..., SingleQubitGate]: ...  # noqa: N802

    def decompose(self, gate: Gate) -> list[Gate]:
        """Decomposes a single-qubit gate into (at most) three single-qubit gates following the
        R$a$-R$b$-R$a$ decomposition, where [$ab$] are in $\\{x,y,z\\}$ and $a$ is not equal to $b$.

        For instance, the ZYZ decomposer decomposes a single-qubit gate into Rz-Ry-Rz.

        Args:
            gate (Gate): Single-qubit gate to decompose.

        Returns:
            A sequence of (at most) three gates, following the R$a$-R$b$-R$a$ decomposition.

        """
        if not isinstance(gate, SingleQubitGate):
            return [gate]

        theta_a1, theta_b, theta_a2 = self._determine_rotation_angles(gate.bsr.axis, gate.bsr.angle)
        return filter_out_identities(
            [
                self.Ra(gate.qubit, theta_a1),
                self.Rb(gate.qubit, theta_b),
                self.Ra(gate.qubit, theta_a2),
            ]
        )

    def _b_and_c_components_in_negative_octant(self, b_component: float, c_component: float) -> bool:
        """Checks if the values for
        the B and C axes fall in one of the two negative octants (a positive or negative, and B and
        C negative, or one of them zero).

        Args:
            b_component (float): Value of the B component.
            c_component (float): Value of the C component.

        Returns:
            True if the values for axis B and C are both negative or zero, but not zero at the same time.
            False otherwise.
        """
        return (
            (b_component < 0 or abs(b_component) < ATOL)
            and (c_component < 0 or abs(c_component) < ATOL)
            and not (abs(b_component) < ATOL and abs(c_component) < ATOL)
        )

    def _determine_rotation_angles(self, axis: AxisLike, theta: float) -> tuple[float, float, float]:
        """Determines the rotation angles for the R$a$-R$b$-R$a$ decomposition.

        Args:
            axis (AxisLike): Axis of the Bloch sphere rotation.
            theta (float): Angle $\\theta$ of the Bloch sphere rotation.

        Returns:
            The rotation angles $\\theta_{a_1}$, $\\theta_b$, and $\\theta_{a_2}$ around axes $a$,
            $b$, and $a$, respectively.

        """
        if not (-math.pi + ATOL < theta <= math.pi + ATOL):
            msg = f"angle {theta!r} is not normalized between -pi and pi"
            raise ValueError(msg)

        component_a, component_b, component_c = self._set_components(axis)

        theta_b = 2 * acos(math.cos(theta / 2) * math.sqrt(1 + (component_a * math.tan(theta / 2)) ** 2))
        theta_b = math.copysign(theta_b, theta)

        p = 2 * math.atan2(component_a * math.sin(theta / 2), math.cos(theta / 2))
        if abs(math.sin(theta_b / 2)) < ATOL:
            m = p
        else:
            m = 2 * acos(float(component_b) * math.sin(theta / 2) / math.sin(theta_b / 2))
            if math.pi - abs(m) > ATOL:
                ret_sign = 2 * math.atan2(component_c, component_a)
                m = math.copysign(m, ret_sign)

        if are_axes_consecutive(self.index_a, self.index_b):
            m = -m

        theta_a1 = (p + m) / 2
        theta_a2 = p - theta_a1

        if self._b_and_c_components_in_negative_octant(component_b, component_c):
            theta_a1, theta_a2 = theta_a2, theta_a1

        return theta_a1, theta_b, theta_a2

    def _find_unused_index(self) -> int:
        """Finds the index of the axis component that is not used in the decomposition.
        For example, for the Rz-Ry-Rz decomposition, the index returned is 0 (since it is x).

        Returns:
            Index of the axis component that is not used in the decomposition.

        """
        return ({0, 1, 2} - {self.index_a, self.index_b}).pop()

    def _set_components(self, axis: AxisLike) -> tuple[Any, Any, Any]:
        """Sets a new rotation axis (a, b, c).

        For instance, for an Rz-Ry-Rz decomposition the initial axis (x, y, z) is set to
        (a, b, c) = (z, y, x).

        Parameters:
            axis (AxisLike): Axis of a Bloch sphere rotation

         Returns:
             A triplet (a, b, c) where a, b, and c are the values of x, y, and z reordered.

        """
        axis_ = Axis(axis)
        return axis_[self.index_a], axis_[self.index_b], axis_[self._find_unused_index()]


class XYXDecomposer(ABADecomposer):
    """Decomposes single-qubit gates into a Rx-Ry-Rx decomposition."""

    @property
    def Ra(self) -> Callable[..., SingleQubitGate]:  # noqa: N802
        return Rx

    @property
    def Rb(self) -> Callable[..., SingleQubitGate]:  # noqa: N802
        return Ry


class XZXDecomposer(ABADecomposer):
    """Decomposes single-qubit gates into a Rx-Rz-Rx decomposition."""

    @property
    def Ra(self) -> Callable[..., SingleQubitGate]:  # noqa: N802
        return Rx

    @property
    def Rb(self) -> Callable[..., SingleQubitGate]:  # noqa: N802
        return Rz


class YXYDecomposer(ABADecomposer):
    """Decomposes single-qubit gates into a Ry-Rx-Ry decomposition."""

    @property
    def Ra(self) -> Callable[..., SingleQubitGate]:  # noqa: N802
        return Ry

    @property
    def Rb(self) -> Callable[..., SingleQubitGate]:  # noqa: N802
        return Rx


class YZYDecomposer(ABADecomposer):
    """Decomposes single-qubit gates into a Ry-Rz-Ry decomposition."""

    @property
    def Ra(self) -> Callable[..., SingleQubitGate]:  # noqa: N802
        return Ry

    @property
    def Rb(self) -> Callable[..., SingleQubitGate]:  # noqa: N802
        return Rz


class ZXZDecomposer(ABADecomposer):
    """Decomposes single-qubit gates into a Rz-Rx-Rz decomposition."""

    @property
    def Ra(self) -> Callable[..., SingleQubitGate]:  # noqa: N802
        return Rz

    @property
    def Rb(self) -> Callable[..., SingleQubitGate]:  # noqa: N802
        return Rx


class ZYZDecomposer(ABADecomposer):
    """Decomposes single-qubit gates into a Rz-Ry-Rz decomposition."""

    @property
    def Ra(self) -> Callable[..., SingleQubitGate]:  # noqa: N802
        return Rz

    @property
    def Rb(self) -> Callable[..., SingleQubitGate]:  # noqa: N802
        return Ry
