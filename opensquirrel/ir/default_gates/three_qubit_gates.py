import numpy as np

from opensquirrel.ir.expression import Qubit, QubitLike
from opensquirrel.ir.semantics import MatrixGateSemantic
from opensquirrel.ir.three_qubit_gate import ThreeQubitGate


class CCX(ThreeQubitGate):
    def __init__(self, control_qubit_0: QubitLike, control_qubit_1: QubitLike, target_qubit: QubitLike) -> None:
        super().__init__(
            qubit0=control_qubit_0,
            qubit1=control_qubit_1,
            qubit2=target_qubit,
            gate_semantic=MatrixGateSemantic(
                matrix=np.array(
                    [
                        [1, 0, 0, 0, 0, 0, 0, 0],
                        [0, 1, 0, 0, 0, 0, 0, 0],
                        [0, 0, 1, 0, 0, 0, 0, 0],
                        [0, 0, 0, 1, 0, 0, 0, 0],
                        [0, 0, 0, 0, 1, 0, 0, 0],
                        [0, 0, 0, 0, 0, 1, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 1],
                        [0, 0, 0, 0, 0, 0, 1, 0],
                    ],
                ),
            ),
            name="CCX",
        )
        self.control_qubit_0 = Qubit(control_qubit_0)
        self.control_qubit_1 = Qubit(control_qubit_1)
        self.target_qubit = Qubit(target_qubit)


class CSWAP(ThreeQubitGate):
    def __init__(self, control_qubit: QubitLike, qubit_0: QubitLike, qubit_1: QubitLike) -> None:
        super().__init__(
            qubit0=control_qubit,
            qubit1=qubit_0,
            qubit2=qubit_1,
            gate_semantic=MatrixGateSemantic(
                matrix=np.array(
                    [
                        [1, 0, 0, 0, 0, 0, 0, 0],
                        [0, 1, 0, 0, 0, 0, 0, 0],
                        [0, 0, 1, 0, 0, 0, 0, 0],
                        [0, 0, 0, 1, 0, 0, 0, 0],
                        [0, 0, 0, 0, 1, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 1, 0],
                        [0, 0, 0, 0, 0, 1, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 1],
                    ],
                ),
            ),
            name="CSWAP",
        )
        self.control_qubit = Qubit(control_qubit)
        self.qubit_0 = Qubit(qubit_0)
        self.qubit_1 = Qubit(qubit_1)
