import math
from typing import List

import numpy as np

from opensquirrel.common import Can1
from opensquirrel.gates import MultiQubitMatrixSemantic, Semantic, SingleQubitAxisAngleSemantic


def get_reduced_ket(ket: int, qubits: List[int]) -> int:
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
        >>> get_reduced_ket(1, [0])         # 0b01
        1
        >>> get_reduced_ket(1111, [2])      # 0b01
        1
        >>> get_reduced_ket(1111, [5])      # 0b0
        0
        >>> get_reduced_ket(1111, [2, 5])   # 0b01
        1
        >>> get_reduced_ket(101, [1, 0])    # 0b10
        2
        >>> get_reduced_ket(101, [0, 1])    # 0b01
        1
    """
    reduced_ket = 0
    for i, qubit in enumerate(qubits):
        reduced_ket |= ((ket & (1 << qubit)) >> qubit) << i

    return reduced_ket


def expand_ket(base_ket: int, reduced_ket: int, qubits: List[int]) -> int:
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
        >>> expand_ket(0b00000, 0b0, [5])   # 0b000000
        0
        >>> expand_ket(0b00000, 0b1, [5])   # 0b100000
        32
        >>> expand_ket(0b00111, 0b0, [5])   # 0b000111
        7
        >>> expand_ket(0b00111, 0b1, [5])   # 0b100111
        39
        >>> expand_ket(0b0000, 0b000, [1, 2, 3])    # 0b0000
        0
        >>> expand_ket(0b0000, 0b001, [1, 2, 3])    # 0b0010
        2
        >>> expand_ket(0b0000, 0b011, [1, 2, 3])    # 0b0110
        6
        >>> expand_ket(0b0000, 0b101, [1, 2, 3])   # 0b1010
        10
        >>> expand_ket(0b0001, 0b101, [1, 2, 3])   # 0b1011
        11
    """
    expanded_ket = base_ket
    for i, qubit in enumerate(qubits):
        expanded_ket &= ~(1 << qubit)  # Erase bit.
        expanded_ket |= ((reduced_ket & (1 << i)) >> i) << qubit  # Set bit to value from reduced_ket.

    return expanded_ket


def get_expanded_matrix(semantic: Semantic, qubit_operands: List[int], number_of_qubits: int) -> np.ndarray:
    """
    Compute the unitary matrix corresponding to the gate applied to those qubit operands, taken among any number of qubits.
    This can be used for, e.g.,
    - testing,
    - permuting the operands of multi-qubit gates,
    - simulating a circuit (simulation in this way is inefficient for large numbers of qubits).

    Args:
        semantic: The semantic of the gate.
        qubit_operands: The qubit indices on which the gate operates.
        number_of_qubits: The total number of qubits.

    Examples:
        >>> X = SingleQubitAxisAngleSemantic((1, 0, 0), math.pi, math.pi / 2)
        >>> get_expanded_matrix(X, [1], 2).astype(int)           # X q[1]
        array([[0, 0, 1, 0],
               [0, 0, 0, 1],
               [1, 0, 0, 0],
               [0, 1, 0, 0]])

        >>> CNOT = MultiQubitMatrixSemantic(np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]]))
        >>> get_expanded_matrix(CNOT, [0, 2], 3)     # CNOT q[0], q[2]
        array([[1, 0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 1, 0, 0],
               [0, 0, 1, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 0, 1],
               [0, 0, 0, 0, 1, 0, 0, 0],
               [0, 1, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 1, 0],
               [0, 0, 0, 1, 0, 0, 0, 0]])
        >>> get_expanded_matrix(CNOT, [1, 2], 3)     # CNOT q[1], q[2]
        array([[1, 0, 0, 0, 0, 0, 0, 0],
               [0, 1, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 1, 0],
               [0, 0, 0, 0, 0, 0, 0, 1],
               [0, 0, 0, 0, 1, 0, 0, 0],
               [0, 0, 0, 0, 0, 1, 0, 0],
               [0, 0, 1, 0, 0, 0, 0, 0],
               [0, 0, 0, 1, 0, 0, 0, 0]])
    """
    if isinstance(semantic, SingleQubitAxisAngleSemantic):
        assert len(qubit_operands) == 1

        which_qubit = qubit_operands[0]

        axis, angle, phase = semantic.axis, semantic.angle, semantic.phase
        result = np.kron(
            np.kron(np.eye(1 << (number_of_qubits - which_qubit - 1)), Can1(axis, angle, phase)),
            np.eye(1 << which_qubit),
        )
        assert result.shape == (1 << number_of_qubits, 1 << number_of_qubits)
        return result

    assert isinstance(semantic, MultiQubitMatrixSemantic)

    # The convention is to write gate matrices with operands reversed.
    # For instance, the first operand of CNOT is the control qubit, and this is written as
    #   1, 0, 0, 0
    #   0, 1, 0, 0
    #   0, 0, 0, 1
    #   0, 0, 1, 0
    # which corresponds to control being q[1] and target being q[0],
    # since qubit #i corresponds to the i-th LEAST significant bit.
    qubit_operands.reverse()

    m = semantic.matrix

    assert m.shape == (1 << len(qubit_operands), 1 << len(qubit_operands))

    expanded_matrix = np.zeros((1 << number_of_qubits, 1 << number_of_qubits), dtype=m.dtype)

    for expanded_matrix_column in range(expanded_matrix.shape[1]):
        small_matrix_col = get_reduced_ket(expanded_matrix_column, qubit_operands)

        for small_matrix_row, value in enumerate(m[:, small_matrix_col]):
            expanded_matrix_row = expand_ket(expanded_matrix_column, small_matrix_row, qubit_operands)
            expanded_matrix[expanded_matrix_row][expanded_matrix_column] = value

    assert expanded_matrix.shape == (1 << number_of_qubits, 1 << number_of_qubits)
    return expanded_matrix
