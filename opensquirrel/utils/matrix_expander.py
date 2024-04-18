import math
from typing import List

import numpy as np

from opensquirrel.common import can1
from opensquirrel.decomposer.general_decomposer import _QubitReIndexer
from opensquirrel.squirrel_ir import BlochSphereRotation, ControlledGate, Gate, Qubit, SquirrelIR, SquirrelIRVisitor


def get_reduced_ket(ket: int, qubits: List[Qubit]) -> int:
    """
    Given a quantum ket represented by its corresponding base-10 integer, this computes the reduced ket
    where only the given qubits appear, in order.
    Roughly equivalent to the `pext` assembly instruction (bits extraction).

    Args:
        ket: A quantum ket, represented by its corresponding non-negative integer.
             By convention, qubit #0 corresponds to the least significant bit.
        qubits: The indices of the qubits to extract. Order matters.

    Returns:
        The non-negative integer corresponding to the reduced ket.

    Examples:
        >>> get_reduced_ket(1, [Qubit(0)])         # 0b01
        1
        >>> get_reduced_ket(1111, [Qubit(2)])      # 0b01
        1
        >>> get_reduced_ket(1111, [Qubit(5)])      # 0b0
        0
        >>> get_reduced_ket(1111, [Qubit(2), Qubit(5)])   # 0b01
        1
        >>> get_reduced_ket(101, [Qubit(1), Qubit(0)])    # 0b10
        2
        >>> get_reduced_ket(101, [Qubit(0), Qubit(1)])    # 0b01
        1
    """
    reduced_ket = 0
    for i, qubit in enumerate(qubits):
        reduced_ket |= ((ket & (1 << qubit.index)) >> qubit.index) << i

    return reduced_ket


def expand_ket(base_ket: int, reduced_ket: int, qubits: List[Qubit]) -> int:
    """
    Given a base quantum ket on n qubits and a reduced ket on a subset of those qubits, this computes the expanded ket
    where the reduction qubits and the other qubits are set based on the reduced ket and the base ket, respectively.
    Roughly equivalent to the `pdep` assembly instruction (bits deposit).

    Args:
        base_ket: A quantum ket, represented by its corresponding non-negative integer.
                  By convention, qubit #0 corresponds to the least significant bit.
        reduced_ket: A quantum ket, represented by its corresponding non-negative integer.
                     By convention, qubit #0 corresponds to the least significant bit.
        qubits: The indices of the qubits to expand from the reduced ket. Order matters.

    Returns:
        The non-negative integer corresponding to the expanded ket.

    Examples:
        >>> expand_ket(0b00000, 0b0, [Qubit(5)])   # 0b000000
        0
        >>> expand_ket(0b00000, 0b1, [Qubit(5)])   # 0b100000
        32
        >>> expand_ket(0b00111, 0b0, [Qubit(5)])   # 0b000111
        7
        >>> expand_ket(0b00111, 0b1, [Qubit(5)])   # 0b100111
        39
        >>> expand_ket(0b0000, 0b000, [Qubit(1), Qubit(2), Qubit(3)])    # 0b0000
        0
        >>> expand_ket(0b0000, 0b001, [Qubit(1), Qubit(2), Qubit(3)])    # 0b0010
        2
        >>> expand_ket(0b0000, 0b011, [Qubit(1), Qubit(2), Qubit(3)])    # 0b0110
        6
        >>> expand_ket(0b0000, 0b101, [Qubit(1), Qubit(2), Qubit(3)])   # 0b1010
        10
        >>> expand_ket(0b0001, 0b101, [Qubit(1), Qubit(2), Qubit(3)])   # 0b1011
        11
    """
    expanded_ket = base_ket
    for i, qubit in enumerate(qubits):
        expanded_ket &= ~(1 << qubit.index)  # Erase bit.
        expanded_ket |= ((reduced_ket & (1 << i)) >> i) << qubit.index  # Set bit to value from reduced_ket.

    return expanded_ket


class MatrixExpander(SquirrelIRVisitor):
    def __init__(self, number_of_qubits: int):
        self.number_of_qubits = number_of_qubits

    def visit_bloch_sphere_rotation(self, rot):
        assert rot.qubit.index < self.number_of_qubits

        result = np.kron(
            np.kron(np.eye(1 << (self.number_of_qubits - rot.qubit.index - 1)), can1(rot.axis, rot.angle, rot.phase)),
            np.eye(1 << rot.qubit.index),
        )
        assert result.shape == (1 << self.number_of_qubits, 1 << self.number_of_qubits)
        return result

    def visit_controlled_gate(self, gate):
        assert gate.control_qubit.index < self.number_of_qubits

        expanded_matrix = gate.target_gate.accept(self)
        for col_index, col in enumerate(expanded_matrix.T):
            if col_index & (1 << gate.control_qubit.index) == 0:
                col[:] = 0
                col[col_index] = 1
        return expanded_matrix

    def visit_matrix_gate(self, gate):
        # The convention is to write gate matrices with operands reversed.
        # For instance, the first operand of CNOT is the control qubit, and this is written as
        #   1, 0, 0, 0
        #   0, 1, 0, 0
        #   0, 0, 0, 1
        #   0, 0, 1, 0
        # which corresponds to control being q[1] and target being q[0],
        # since qubit #i corresponds to the i-th LEAST significant bit.
        qubit_operands = list(reversed(gate.operands))

        assert all(q.index < self.number_of_qubits for q in qubit_operands)

        m = gate.matrix

        assert m.shape == (1 << len(qubit_operands), 1 << len(qubit_operands))

        expanded_matrix = np.zeros((1 << self.number_of_qubits, 1 << self.number_of_qubits), dtype=m.dtype)

        for expanded_matrix_column in range(expanded_matrix.shape[1]):
            small_matrix_col = get_reduced_ket(expanded_matrix_column, qubit_operands)

            for small_matrix_row, value in enumerate(m[:, small_matrix_col]):
                expanded_matrix_row = expand_ket(expanded_matrix_column, small_matrix_row, qubit_operands)
                expanded_matrix[expanded_matrix_row][expanded_matrix_column] = value

        assert expanded_matrix.shape == (1 << self.number_of_qubits, 1 << self.number_of_qubits)
        return expanded_matrix


def get_matrix(gate: Gate, number_of_qubits: int) -> np.ndarray:
    """
    Compute the unitary matrix corresponding to the gate applied to those qubit operands, taken among any number of
    qubits. This can be used for, e.g.,
    - testing,
    - permuting the operands of multi-qubit gates,
    - simulating a circuit (simulation in this way is inefficient for large numbers of qubits).

    Args:
        gate: The gate, including the qubits on which it is operated on.
        number_of_qubits: The total number of qubits.

    Examples:
        >>> X = lambda q: BlochSphereRotation(qubit=q, axis=(1, 0, 0), angle=math.pi, phase=math.pi / 2)
        >>> get_matrix(X(Qubit(1)), 2).astype(int)           # X q[1]
        array([[0, 0, 1, 0],
               [0, 0, 0, 1],
               [1, 0, 0, 0],
               [0, 1, 0, 0]])

        >>> CNOT02 = ControlledGate(Qubit(0), X(Qubit(2)))
        >>> get_matrix(CNOT02, 3).astype(int)     # CNOT q[0], q[2]
        array([[1, 0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 1, 0, 0],
               [0, 0, 1, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 0, 1],
               [0, 0, 0, 0, 1, 0, 0, 0],
               [0, 1, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 1, 0],
               [0, 0, 0, 1, 0, 0, 0, 0]])
        >>> get_matrix(ControlledGate(Qubit(1), X(Qubit(2))), 3).astype(int)     # CNOT q[1], q[2]
        array([[1, 0, 0, 0, 0, 0, 0, 0],
               [0, 1, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 1, 0],
               [0, 0, 0, 0, 0, 0, 0, 1],
               [0, 0, 0, 0, 1, 0, 0, 0],
               [0, 0, 0, 0, 0, 1, 0, 0],
               [0, 0, 1, 0, 0, 0, 0, 0],
               [0, 0, 0, 1, 0, 0, 0, 0]])
    """

    expander = MatrixExpander(number_of_qubits)
    return gate.accept(expander)


def get_matrix_after_qubit_remapping(replacement: List[Gate], qubit_mappings: List[Qubit]):
    from opensquirrel.circuit_matrix_calculator import get_circuit_matrix

    replacement_ir = SquirrelIR(number_of_qubits=len(qubit_mappings), qubit_register_name="q_temp")
    qubit_remapper = _QubitReIndexer(qubit_mappings)
    for gate in replacement:
        gate_with_remapped_qubits = gate.accept(qubit_remapper)
        replacement_ir.add_gate(gate_with_remapped_qubits)

    return get_circuit_matrix(replacement_ir)
