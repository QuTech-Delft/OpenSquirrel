import warnings
from math import pi
from typing import Any, SupportsFloat, SupportsInt

import numpy as np

from opensquirrel.common import normalize_angle
from opensquirrel.ir import Gate
from opensquirrel.ir.default_gates import X, Z
from opensquirrel.ir.default_gates.single_qubit_gates import SingleQubitGate
from opensquirrel.ir.expression import Expression, Float, Int, Qubit, QubitLike
from opensquirrel.ir.ir import IRVisitor
from opensquirrel.ir.semantics.bsr import BsrAngleParam
from opensquirrel.ir.semantics.controlled_gate import ControlledGate
from opensquirrel.ir.semantics.matrix_gate import MatrixGate


# The R gate is only defined for the purpose of defining the CR and CRk gates and does not appear as a separate gate in
# the default instruction set.
class TwoQubitGate(Gate):
    pass


class R(SingleQubitGate):
    def __init__(self, qubit: QubitLike, theta: SupportsFloat) -> None:
        super().__init__(qubit=qubit, name="R")
        phase = float(theta) / 2
        self.bsr = BsrAngleParam(axis=(0, 0, 1), angle=theta, phase=phase)


class SWAP(MatrixGate):
    def __init__(self, qubit_0: QubitLike, qubit_1: QubitLike) -> None:
        MatrixGate.__init__(
            self,
            matrix=np.array(
                [
                    [1, 0, 0, 0],
                    [0, 0, 1, 0],
                    [0, 1, 0, 0],
                    [0, 0, 0, 1],
                ],
            ),
            operands=[qubit_0, qubit_1],
            name="SWAP",
        )
        self.qubit_0 = Qubit(qubit_0)
        self.qubit_1 = Qubit(qubit_1)

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return self.qubit_0, self.qubit_1

    def get_qubit_operands(self) -> list[Qubit]:
        return [self.qubit_0, self.qubit_1]

    def accept(self, visitor: IRVisitor) -> Any:
        visit_parent = super().accept(visitor)
        return visit_parent if visit_parent is not None else visitor.visit_swap(self)


class CNOT(ControlledGate):
    def __init__(self, control_qubit: QubitLike, target_qubit: QubitLike) -> None:
        ControlledGate.__init__(self, control_qubit=control_qubit, target_gate=X(target_qubit), name="CNOT")
        self.control_qubit = Qubit(control_qubit)
        self.target_qubit = Qubit(target_qubit)

    def accept(self, visitor: IRVisitor) -> Any:
        visit_parent = super().accept(visitor)
        return visit_parent if visit_parent is not None else visitor.visit_cnot(self)


class CZ(ControlledGate):
    def __init__(self, control_qubit: QubitLike, target_qubit: QubitLike) -> None:
        ControlledGate.__init__(self, control_qubit=control_qubit, target_gate=Z(target_qubit), name="CZ")
        self.control_qubit = Qubit(control_qubit)
        self.target_qubit = Qubit(target_qubit)

    def accept(self, visitor: IRVisitor) -> Any:
        visit_parent = super().accept(visitor)
        return visit_parent if visit_parent is not None else visitor.visit_cz(self)


class CR(ControlledGate):
    def __init__(self, control_qubit: QubitLike, target_qubit: QubitLike, theta: SupportsFloat) -> None:
        ControlledGate.__init__(self, control_qubit=control_qubit, target_gate=R(target_qubit, theta), name="CR")
        self.control_qubit = Qubit(control_qubit)
        self.target_qubit = Qubit(target_qubit)
        self.theta = Float(normalize_angle(theta))

    def accept(self, visitor: IRVisitor) -> Any:
        visit_parent = super().accept(visitor)
        return visit_parent if visit_parent is not None else visitor.visit_cr(self)


class CRk(ControlledGate):
    def __init__(self, control_qubit: QubitLike, target_qubit: QubitLike, k: SupportsInt) -> None:
        if not isinstance(k, (int, Int)):
            warnings.warn(
                f"value of parameter 'k' is not an integer: got {type(k)!r} instead.", UserWarning, stacklevel=2
            )
        theta = normalize_angle(2 * pi / (2 ** int(k)))
        ControlledGate.__init__(self, control_qubit=control_qubit, target_gate=R(target_qubit, theta), name="CRk")
        self.control_qubit = Qubit(control_qubit)
        self.target_qubit = Qubit(target_qubit)
        self.k = Int(k)

    def accept(self, visitor: IRVisitor) -> Any:
        visit_parent = super().accept(visitor)
        return visit_parent if visit_parent is not None else visitor.visit_crk(self)
