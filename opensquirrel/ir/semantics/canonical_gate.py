from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
from numpy.typing import NDArray

from opensquirrel.ir.expression import BaseAxis
from opensquirrel.ir.semantics.gate_semantic import GateSemantic

if TYPE_CHECKING:
    from opensquirrel.ir import AxisLike, IRVisitor
    from opensquirrel.ir.semantics import BlochSphereRotation


class CanonicalAxis(BaseAxis):
    restrict: bool = True

    @staticmethod
    def in_weyl_chamber(tx: float, ty: float, tz: float) -> bool:
        """Checks if the canonical axis is in the Weyl chamber.

        Returns:
            True if the canonical axis is in the Weyl chamber, False otherwise.

        """
        return 1 / 2 >= tx >= ty >= tz >= 0 or 1 / 2 >= (1 - tx) >= ty >= tz > 0

    @staticmethod
    def parse(axis: AxisLike) -> NDArray[np.float64]:
        """Parse and validate an `AxisLike`.

        Checks if the axis can be cast to a 1DArray of length 3, raise an error otherwise.
        After casting to an array, the elements of the canonical axis are restricted to the Weyl chamber.

        Args:
            axis (AxisLike): Axis to validate and parse.

        Returns:
            Parsed axis to 1DArray of length 3.

        Raises:
            TypeError: If the axis cannot be cast to an ArrayLike.
            ValueError: If the axis cannot be flattened to length 3.

        """

        if isinstance(axis, CanonicalAxis):
            return axis.value

        try:
            axis = np.asarray(axis, dtype=float)
        except (ValueError, TypeError) as e:
            msg = "axis requires an ArrayLike"
            raise TypeError(msg) from e
        axis = axis.flatten()
        if len(axis) != 3:
            msg = f"axis has size {len(axis)!r}: requires an ArrayLike of length 3"
            raise ValueError(msg)
        if CanonicalAxis.restrict:
            return CanonicalAxis.restrict_to_weyl_chamber(axis)
        return axis

    @staticmethod
    def restrict_to_weyl_chamber(axis: NDArray[np.float64]) -> NDArray[np.float64]:
        """Restricts the given axis to the Weyl chamber.

        The six rules that are (implicitly) used are:

        1. The canonical parameters are periodic with a period of 2 (neglecting
            a global phase).
        2. $\\text{Can}(t_x, t_y, t_z)\\sim\\text{Can}(t_x - 1, t_y, t_z)$ (for any parameter)
        3. $\\text{Can}(t_x, t_y, t_z)\\sim\\text{Can}(t_x, -t_y, -t_z)$ (for any pair of parameters)
        4. $\\text{Can}(t_x, t_y, t_z)\\sim\\text{Can}(t_y, t_x, t_z)$ (for any pair of parameters)
        5. $\\text{Can}(t_x, t_y, 0)\\sim\\text{Can}(1 - t_x, t_y, 0)$
        6. $\\text{Can}(t_x, t_y, t_z) * \\text{Can}(t_x', t_y', t_z') =
        \\text{Can}(t_x + t_x', t_y + t_y', t_z + t_z')$

        Note:
            Based on the rules described in
            [Quantum Gates by G.E. Crooks (2024), Section 5](https://threeplusone.com/pubs/on_gates.pdf).

        Args:
            axis (NDArray[np.float64]): Axis to restrict to the Weyl chamber.

        Returns:
           Axis restricted to the Weyl chamber.

        """
        axis = (axis + 1) % 2 - 1

        while (axis < 0).any():
            axis = np.where(axis < 0, axis - 1, axis)
            axis = (axis + 1) % 2 - 1

        axis = np.sort(axis)[::-1]
        match sum(t > 1 / 2 for t in axis):
            case 1:
                axis[0] = 1 - axis[0]
            case 2:
                axis[0], axis[2] = axis[2], axis[0]
                axis[1:] = 1 - axis[1:]
            case 3:
                axis = 1 - axis

        return np.sort(axis)[::-1]

    def accept(self, visitor: IRVisitor) -> Any:
        """Accepts visitor and processes this IR node."""
        return visitor.visit_canonical_axis(self)


class CanonicalGateSemantic(GateSemantic):
    def __init__(self, axis: AxisLike, rotations: list[BlochSphereRotation] | None = None) -> None:
        self.axis = CanonicalAxis(axis)
        self.rotations = rotations

    def accept(self, visitor: IRVisitor) -> Any:
        """Accepts visitor and processes this IR node."""
        return visitor.visit_canonical_gate_semantic(self)

    def is_identity(self) -> bool:
        """Checks if the canonical gate semantic represents an identity operation.

        Returns:
            True if the canonical gate semantic represents an identity operation, False otherwise.

        """
        return self.axis == CanonicalAxis((0, 0, 0))

    def __repr__(self) -> str:
        return f"CanonicalGateSemantic(axis={self.axis})"
