from typing import Any

import numpy as np
from numpy.typing import NDArray

from opensquirrel.common import repr_round
from opensquirrel.ir import AxisLike, IRVisitor, Qubit, QubitLike
from opensquirrel.ir.expression import BaseAxis, Expression
from opensquirrel.ir.unitary import Gate


class CanonicalAxis(BaseAxis):
    @staticmethod
    def parse(axis: AxisLike) -> NDArray[np.float64]:
        """Parse and validate an ``AxisLike``.

        Check if the `axis` can be cast to a 1DArray of length 3, raise an error otherwise.
        After casting to an array, the elements of the canonical axis are restricted to the Weyl chamber.

        Args:
            axis: ``AxisLike`` to validate and parse.

        Returns:
            Parsed axis represented as a 1DArray of length 3.
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
            msg = f"axis requires an ArrayLike of length 3, but received an ArrayLike of length {len(axis)}"
            raise ValueError(msg)

        return CanonicalAxis.restrict_to_weyl_chamber(axis)

    @staticmethod
    def restrict_to_weyl_chamber(axis: NDArray[np.float64]) -> NDArray[np.float64]:
        """Restrict the given axis to the Weyl chamber. The six rules that are
        (implicitly) used are:
            1. The canonical parameters are periodic with a period of 2 (neglecting
               a global phase).
            2. Can(tx, ty, tz) ~ Can(tx - 1, ty, tz) (for any parameter)
            3. Can(tx, ty, tz) ~ Can(tx, -ty, -tz) (for any pair of parameters)
            4. Can(tx, ty, tz) ~ Can(ty, tx, tz) (for any pair of parameters)
            5. Can(tx, ty, 0) ~ Can(1 - tx, ty, 0)
            6. Can(tx, ty, tz) x Can(tx', ty', tz') = Can(tx + tx', ty + ty', tz + tz')
               (here x represents matrix multiplication)

        Based on the rules described in Chapter 5 of https://threeplusone.com/pubs/on_gates.pdf
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
        return visitor.visit_canonical_axis(self)


class CanonicalGate(Gate):
    def __init__(self, qubit_0: QubitLike, qubit_1: QubitLike, axis: AxisLike, name: str = "CanonicalGate") -> None:
        Gate.__init__(self, name)
        self.qubit_0 = Qubit(qubit_0)
        self.qubit_1 = Qubit(qubit_1)
        self.axis = CanonicalAxis(axis)

        if self._check_repeated_qubit_operands([self.qubit_0, self.qubit_1]):
            msg = "the two qubits cannot be the same"
            raise ValueError(msg)

    def __repr__(self) -> str:
        return f"{self.name}(q0={self.qubit_0}, q1={self.qubit_1}, axis={repr_round(self.axis)})"

    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_canonical_gate(self)

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return (self.qubit_0, self.qubit_1, self.axis)

    def get_qubit_operands(self) -> list[Qubit]:
        return [self.qubit_0, self.qubit_1]

    def is_identity(self) -> bool:
        return self.axis == CanonicalAxis(0, 0, 0)
