import warnings
from math import pi
from typing import SupportsFloat, SupportsInt

import numpy as np

from opensquirrel.common import normalize_angle
from opensquirrel.ir.default_gates import X, Z
from opensquirrel.ir.expression import Expression, Float, Int, Qubit, QubitLike
from opensquirrel.ir.semantics import ControlledGateSemantic, MatrixGateSemantic
from opensquirrel.ir.semantics.bsr import BsrAngleParam
from opensquirrel.ir.single_qubit_gate import SingleQubitGate
from opensquirrel.ir.two_qubit_gate import TwoQubitGate


# The R gate is only defined for the purpose of defining the CR and CRk gates and does not appear as a separate gate in
# the default instruction set.
class R(SingleQubitGate):
    def __init__(self, qubit: QubitLike, theta: SupportsFloat) -> None:
        phase = float(theta) / 2
        super().__init__(qubit=qubit, gate_semantic=BsrAngleParam(axis=(0, 0, 1), angle=theta, phase=phase), name="R")


class SWAP(TwoQubitGate):
    def __init__(self, qubit_0: QubitLike, qubit_1: QubitLike) -> None:
        super().__init__(
            qubit0=qubit_0,
            qubit1=qubit_1,
            gate_semantic=MatrixGateSemantic(
                matrix=np.array(
                    [
                        [1, 0, 0, 0],
                        [0, 0, 1, 0],
                        [0, 1, 0, 0],
                        [0, 0, 0, 1],
                    ],
                ),
            ),
            name="SWAP",
        )
        self.qubit_0 = Qubit(qubit_0)
        self.qubit_1 = Qubit(qubit_1)


class CNOT(TwoQubitGate):
    def __init__(self, control_qubit: QubitLike, target_qubit: QubitLike) -> None:
        super().__init__(
            qubit0=control_qubit,
            qubit1=target_qubit,
            gate_semantic=ControlledGateSemantic(X(target_qubit)),
            name="CNOT",
        )
        self.control_qubit = Qubit(control_qubit)
        self.target_qubit = Qubit(target_qubit)


class CZ(TwoQubitGate):
    def __init__(self, control_qubit: QubitLike, target_qubit: QubitLike) -> None:
        super().__init__(
            qubit0=control_qubit, qubit1=target_qubit, gate_semantic=ControlledGateSemantic(Z(target_qubit)), name="CZ"
        )
        self.control_qubit = Qubit(control_qubit)
        self.target_qubit = Qubit(target_qubit)


class CR(TwoQubitGate):
    def __init__(self, control_qubit: QubitLike, target_qubit: QubitLike, theta: SupportsFloat) -> None:
        super().__init__(
            qubit0=control_qubit,
            qubit1=target_qubit,
            gate_semantic=ControlledGateSemantic(R(target_qubit, theta)),
            name="CR",
        )
        self.control_qubit = Qubit(control_qubit)
        self.target_qubit = Qubit(target_qubit)
        self.theta = Float(normalize_angle(theta))

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return (*super().arguments, self.theta)


class CRk(TwoQubitGate):
    def __init__(self, control_qubit: QubitLike, target_qubit: QubitLike, k: SupportsInt) -> None:
        if not isinstance(k, (int, Int)):
            warnings.warn(
                f"value of parameter 'k' is not an integer: got {type(k)!r} instead.", UserWarning, stacklevel=2
            )
        theta = normalize_angle(2 * pi / (2 ** int(k)))
        super().__init__(
            qubit0=control_qubit,
            qubit1=target_qubit,
            gate_semantic=ControlledGateSemantic(R(target_qubit, theta)),
            name="CRk",
        )
        self.control_qubit = Qubit(control_qubit)
        self.target_qubit = Qubit(target_qubit)
        self.k = Int(k)

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return (*super().arguments, self.k)
