import numpy as np
from numpy.typing import NDArray

from opensquirrel.squirrel_ir import Comment, Gate, SquirrelIR, SquirrelIRVisitor
from opensquirrel.utils.matrix_expander import get_matrix


class _CircuitMatrixCalculator(SquirrelIRVisitor):
    def __init__(self, number_of_qubits: int) -> None:
        self.number_of_qubits = number_of_qubits
        self.matrix = np.eye(1 << self.number_of_qubits, dtype=np.complex128)

    def visit_gate(self, gate: Gate) -> None:
        big_matrix = get_matrix(gate, number_of_qubits=self.number_of_qubits)
        self.matrix = big_matrix @ self.matrix

    def visit_comment(self, comment: Comment) -> None:
        pass


def get_circuit_matrix(squirrel_ir: SquirrelIR) -> NDArray[np.complex128]:
    """
    Compute the Numpy unitary matrix corresponding to the circuit.
    The size of this matrix grows exponentially with the number of qubits.
    """

    impl = _CircuitMatrixCalculator(squirrel_ir.number_of_qubits)

    squirrel_ir.accept(impl)

    return impl.matrix
