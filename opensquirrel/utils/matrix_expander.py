from __future__ import annotations

import cmath
import math
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

import numpy as np
from numpy.typing import NDArray

from opensquirrel.ir import (
    Axis,
    AxisLike,
    Gate,
    IRVisitor,
    Qubit,
    QubitLike,
)

if TYPE_CHECKING:
    from opensquirrel import (
        CNOT,
        CR,
        CZ,
        SWAP,
        CRk,
    )
    from opensquirrel.ir.semantics import (
        BlochSphereRotation,
        BsrAngleParam,
        BsrFullParams,
        BsrNoParams,
        ControlledGate,
        MatrixGate,
    )


def get_reduced_ket(ket: int, qubits: Iterable[QubitLike]) -> int:
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
        qubit = Qubit(qubit)
        reduced_ket |= ((ket & (1 << qubit.index)) >> qubit.index) << i

    return reduced_ket


def expand_ket(base_ket: int, reduced_ket: int, qubits: Iterable[QubitLike]) -> int:
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
        qubit = Qubit(qubit)
        expanded_ket &= ~(1 << qubit.index)  # erase bit
        expanded_ket |= ((reduced_ket & (1 << i)) >> i) << qubit.index  # set bit to value from reduced_ket

    return expanded_ket


class MatrixExpander(IRVisitor):
    def __init__(self, qubit_register_size: int) -> None:
        self.qubit_register_size = qubit_register_size

    def visit_bloch_sphere_rotation(self, gate: BlochSphereRotation) -> NDArray[np.complex128]:
        if gate.qubit.index >= self.qubit_register_size:
            msg = "index out of range"
            raise IndexError(msg)

        result = np.kron(
            np.kron(
                np.eye(1 << (self.qubit_register_size - gate.qubit.index - 1)),
                can1(gate.axis, gate.angle, gate.phase),
            ),
            np.eye(1 << gate.qubit.index),
        )
        if result.shape != (1 << self.qubit_register_size, 1 << self.qubit_register_size):
            msg = "result has incorrect shape"
            ValueError(msg)
        return np.asarray(result, dtype=np.complex128)

    def visit_bsr_no_params(self, gate: BsrNoParams) -> NDArray[np.complex128]:
        return self.visit_bloch_sphere_rotation(gate)

    def visit_bsr_full_params(self, gate: BsrFullParams) -> NDArray[np.complex128]:
        return self.visit_bloch_sphere_rotation(gate)

    def visit_bsr_angle_param(self, gate: BsrAngleParam) -> NDArray[np.complex128]:
        return self.visit_bloch_sphere_rotation(gate)

    def visit_controlled_gate(self, gate: ControlledGate) -> NDArray[np.complex128]:
        if gate.control_qubit.index >= self.qubit_register_size:
            msg = "index out of range"
            raise IndexError(msg)

        expanded_matrix = gate.target_gate.accept(self)
        for col_index, col in enumerate(expanded_matrix.T):
            if col_index & (1 << gate.control_qubit.index) == 0:
                col[:] = 0
                col[col_index] = 1
        return np.asarray(expanded_matrix, dtype=np.complex128)

    def visit_cnot(self, gate: CNOT) -> Any:
        return self.visit_controlled_gate(gate)

    def visit_cz(self, gate: CZ) -> Any:
        return self.visit_controlled_gate(gate)

    def visit_cr(self, gate: CR) -> Any:
        return self.visit_controlled_gate(gate)

    def visit_crk(self, gate: CRk) -> Any:
        return self.visit_controlled_gate(gate)

    def visit_matrix_gate(self, gate: MatrixGate) -> NDArray[np.complex128]:
        # The convention is to write gate matrices with operands reversed.
        # For instance, the first operand of CNOT is the control qubit, and this is written as
        #   1, 0, 0, 0
        #   0, 1, 0, 0
        #   0, 0, 0, 1
        #   0, 0, 1, 0
        # which corresponds to control being q[1] and target being q[0],
        # since qubit #i corresponds to the i-th least significant bit.
        qubit_operands = list(reversed(gate.operands))

        if any(q.index >= self.qubit_register_size for q in qubit_operands):
            msg = "index out of range"
            raise IndexError(msg)

        m = gate.matrix

        if m.shape != (1 << len(qubit_operands), 1 << len(qubit_operands)):
            msg = (
                f"matrix has incorrect shape."
                f"Expected {(1 << len(qubit_operands), 1 << len(qubit_operands))}, but received {m.shape}"
            )
            raise ValueError(msg)

        expanded_matrix = np.zeros((1 << self.qubit_register_size, 1 << self.qubit_register_size), dtype=m.dtype)

        for expanded_matrix_column in range(expanded_matrix.shape[1]):
            small_matrix_col = get_reduced_ket(expanded_matrix_column, qubit_operands)

            for small_matrix_row, value in enumerate(m[:, small_matrix_col]):
                expanded_matrix_row = expand_ket(expanded_matrix_column, small_matrix_row, qubit_operands)
                expanded_matrix[expanded_matrix_row][expanded_matrix_column] = value

        if expanded_matrix.shape != (1 << self.qubit_register_size, 1 << self.qubit_register_size):
            msg = "expended matrix has incorrect shape"
            raise ValueError(msg)
        return expanded_matrix

    def visit_swap(self, gate: SWAP) -> NDArray[np.complex128]:
        return self.visit_matrix_gate(gate)


X = np.array([[0, 1], [1, 0]])
Y = np.array([[0, -1j], [1j, 0]])
Z = np.array([[1, 0], [0, -1]])


def can1(axis: AxisLike, angle: float, phase: float = 0) -> NDArray[np.complex128]:
    nx, ny, nz = Axis(axis)

    result = cmath.rect(1, phase) * (
        math.cos(angle / 2) * np.identity(2) - 1j * math.sin(angle / 2) * (nx * X + ny * Y + nz * Z)
    )

    return np.asarray(result, dtype=np.complex128)


def get_matrix(gate: Gate, qubit_register_size: int) -> NDArray[np.complex128]:
    """
    Compute the unitary matrix corresponding to the gate applied to those qubit operands, taken among any number of
    qubits. This can be used for, e.g.,
    - testing,
    - permuting the operands of multi-qubit gates,
    - simulating a circuit (simulation in this way is inefficient for large numbers of qubits).

    Args:
        gate: The gate, including the qubits on which it is operated on.
        qubit_register_size: The size of the qubit register.

    Examples:
        >>> X = lambda q: BlochSphereRotation(qubit=q, axis=(1, 0, 0), angle=math.pi, phase=math.pi / 2)
        >>> get_matrix(X(1), 2).astype(int)           # X q[1]
        array([[0, 0, 1, 0],
               [0, 0, 0, 1],
               [1, 0, 0, 0],
               [0, 1, 0, 0]])

        >>> CNOT02 = ControlledGate(0, X(2))
        >>> get_matrix(CNOT02, 3).astype(int)     # CNOT q[0], q[2]
        array([[1, 0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 1, 0, 0],
               [0, 0, 1, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 0, 1],
               [0, 0, 0, 0, 1, 0, 0, 0],
               [0, 1, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 1, 0],
               [0, 0, 0, 1, 0, 0, 0, 0]])
        >>> get_matrix(ControlledGate(1, X(2)), 3).astype(int)     # CNOT q[1], q[2]
        array([[1, 0, 0, 0, 0, 0, 0, 0],
               [0, 1, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 1, 0],
               [0, 0, 0, 0, 0, 0, 0, 1],
               [0, 0, 0, 0, 1, 0, 0, 0],
               [0, 0, 0, 0, 0, 1, 0, 0],
               [0, 0, 1, 0, 0, 0, 0, 0],
               [0, 0, 0, 1, 0, 0, 0, 0]])
    """
    expander = MatrixExpander(qubit_register_size)
    return np.asarray(gate.accept(expander), dtype=np.complex128)
