from opensquirrel.ir import Gate, Qubit, QubitLike, AxisLike, IRVisitor
from opensquirrel.ir.expression import Bit, Expression, BaseAxis
from typing import Any
import numpy as np
from numpy.typing import NDArray


class CanonicalAxis(BaseAxis):

    @staticmethod
    def parse(axis: AxisLike) -> NDArray[np.float64]:
        """Parse and validate an ``AxisLike``.

        Check if the `axis` can be cast to a 1DArray of length 3, raise an error otherwise.
        After casting to an array, the axis is normalized.

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
        
        axis = CanonicalAxis.restrict_to_weyl_chamber(axis)
        return axis
    
    @staticmethod
    def restrict_to_weyl_chamber(axis: NDArray[np.float64]) -> NDArray[np.float64]:
        # TODO
        return axis
    
    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_canonical_axis(self)
 

class CanonicalGate(Gate):
    
    def __init__(self, qubit_0: QubitLike, qubit_1: QubitLike, axis: AxisLike, name: str="CanonicalGate") -> None:
        Gate.__init__(self, name)
        self.qubit_0 = Qubit(qubit_0)
        self.qubit_1 = Qubit(qubit_1)

        self.axis = CanonicalAxis(axis)

    def __repr__(self) -> str:
        return f"{self.name}(q0={self.qubit_0}, q1={self.qubit_1})"
    
    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_canonical_gate(self)
    
    @property
    def arguments(self) -> tuple[Expression, ...]:
        return (self.qubit_0, self.qubit_1,)
    
    def get_qubit_operands(self) -> list[Qubit]:
        return [self.qubit_0, self.qubit_1]
    
    def get_bit_operands(self) -> list[Bit]:
        return []

    def is_identity(self) -> bool:
        return self.axis == CanonicalAxis(0, 0, 0)
    

