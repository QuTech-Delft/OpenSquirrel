import numpy as np

from opensquirrel.circuit import Circuit
from opensquirrel.squirrel_ir import Comment, Gate, SquirrelIR, SquirrelIRVisitor
from opensquirrel.utils.matrix_expander import get_matrix


class _CircuitMatrixCalculator(SquirrelIRVisitor):
    def __init__(self, qubit_register_size):
        self.qubit_register_size = qubit_register_size
        self.matrix = np.eye(1 << self.qubit_register_size, dtype=np.complex128)

    def visit_gate(self, gate: Gate):
        big_matrix = get_matrix(gate, qubit_register_size=self.qubit_register_size)
        self.matrix = big_matrix @ self.matrix

    def visit_comment(self, comment: Comment):
        pass


def get_circuit_matrix(circuit: Circuit):
    """
    Compute the Numpy unitary matrix corresponding to the circuit.
    The size of this matrix grows exponentially with the number of qubits.
    """

    impl = _CircuitMatrixCalculator(circuit.qubit_register_size)

    circuit.squirrel_ir.accept(impl)

    return impl.matrix
