import math

import numpy as np

from opensquirrel.common import Can1
from opensquirrel.gates import MultiQubitMatrixSemantic, Semantic, SingleQubitAxisAngleSemantic


def extract_bits(x: int, bit_indices: [int]) -> int:
    """
    Extract the bits at given indices, placing the bits in order from least to most significant.
    Equivalent to pext instruction.

    Args:
        x: a bitstring
        bit_indices: the indices to extract

    Returns:
        the extracted bits of x in order

    Examples:
        >>> extract_bits(1, [0])   # 0b01
        1
        >>> extract_bits(1111, [2])   # 0b01
        1
        >>> extract_bits(1111, [5])   # 0b0
        0
        >>> extract_bits(1111, [2, 5])   # 0b01
        1
        >>> extract_bits(101, [1, 0])   # 0b10
        2
        >>> extract_bits(101, [0, 1])   # 0b01
        1
    """
    result = 0
    for i in range(len(bit_indices)):
        operand = bit_indices[i]
        result |= ((x & (1 << operand)) >> operand) << i

    return result


def deposit_bits(x: int, bit_indices: [int]) -> int:
    """
    Deposes the bits from x at given indices in the result.
    Equivalent to pdep instruction.

    Args:
        x: a bitstring
        bit_indices: the indices where to deposit the bits of x

    Returns:
        a bitstring whose bit values are taken from the bits of x

    Examples:
        >>> deposit_bits(0b0, [5])   # 0b000000
        0
        >>> deposit_bits(0b1, [5])   # 0b100000
        32
        >>> deposit_bits(0b000, [1, 2, 3])
        0
        >>> deposit_bits(0b001, [1, 2, 3])    # 0b0010
        2
        >>> deposit_bits(0b011, [1, 2, 3])    # 0b0110
        6
        >>> deposit_bits(0b0101, [1, 2, 3])   # 0b1010
        10
    """
    result = 0
    for i in range(len(bit_indices)):
        result |= ((x & (1 << i)) >> i) << bit_indices[i]

    return result


def clear_bits(x: int, bit_indices: [int]) -> int:
    """
    Clears given bits of input.

    Args:
        x: a bitstring
        bit_indices: bit indices to clear

    Returns:
        x with given bits reset to 0

    Examples:
        >>> clear_bits(0b1111, [1, 3])   # 0b0101
        5
    """
    result = x
    for index in bit_indices:
        result &= ~(1 << index)

    return result


def get_expanded_matrix(semantic: Semantic, qubit_operands: [int], total_qubits: int) -> np.ndarray:
    """
    Get the unitary matrix corresponding to the gate applied to those qubit operands.
    This can be used for
    - testing,
    - permuting the operands of a multi-qubit gates,
    - simulating a circuit (simulation in this way is inefficient for large numbers of qubits),
    - ...

    Args:
        semantic: the semantic of the gate
        qubit_operands: the qubit indices on which the gate operates
        total_qubits: the total number of qubits

    Example:
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
            np.kron(np.eye(1 << (total_qubits - which_qubit - 1)), Can1(axis, angle, phase)), np.eye(1 << which_qubit)
        )
        assert result.shape == (1 << total_qubits, 1 << total_qubits)
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

    result = np.zeros((1 << total_qubits, 1 << total_qubits), dtype=m.dtype)

    for input in range(1 << total_qubits):
        small_matrix_col_index = extract_bits(input, qubit_operands)

        col = m[:, small_matrix_col_index]

        for output in range(len(col)):
            value = col[output]

            large_output = clear_bits(input, qubit_operands)

            large_output |= deposit_bits(output, qubit_operands)

            result[large_output][input] = value

    assert result.shape == (1 << total_qubits, 1 << total_qubits)
    return result
