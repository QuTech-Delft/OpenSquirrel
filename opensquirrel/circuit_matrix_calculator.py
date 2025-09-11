from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from opensquirrel.ir import Gate, IRVisitor
from opensquirrel.utils import get_matrix

if TYPE_CHECKING:
    from opensquirrel import CNOT, CR, CZ, SWAP, CRk
    from opensquirrel.circuit import Circuit
    from opensquirrel.ir.semantics import (
        BlochSphereRotation,
        BsrAngleParam,
        BsrFullParams,
        BsrNoParams,
        ControlledGate,
        MatrixGate,
    )


class _CircuitMatrixCalculator(IRVisitor):
    def __init__(self, qubit_register_size: int) -> None:
        self.qubit_register_size = qubit_register_size
        self.matrix = np.eye(1 << self.qubit_register_size, dtype=np.complex128)

    def visit_gate(self, gate: Gate) -> None:
        big_matrix = get_matrix(gate, qubit_register_size=self.qubit_register_size)
        self.matrix = np.asarray(big_matrix @ self.matrix, dtype=np.complex128)

    def visit_bloch_sphere_rotation(self, gate: BlochSphereRotation) -> None:
        self.visit_gate(gate)

    def visit_bsr_no_params(self, gate: BsrNoParams) -> None:
        self.visit_gate(gate)

    def visit_bsr_full_params(self, gate: BsrFullParams) -> None:
        self.visit_gate(gate)

    def visit_bsr_angle_param(self, gate: BsrAngleParam) -> None:
        self.visit_gate(gate)

    def visit_matrix_gate(self, gate: MatrixGate) -> None:
        self.visit_gate(gate)

    def visit_swap(self, gate: SWAP) -> None:
        self.visit_gate(gate)

    def visit_controlled_gate(self, gate: ControlledGate) -> None:
        self.visit_gate(gate)

    def visit_cnot(self, gate: CNOT) -> None:
        self.visit_gate(gate)

    def visit_cz(self, gate: CZ) -> None:
        self.visit_gate(gate)

    def visit_cr(self, gate: CR) -> None:
        self.visit_gate(gate)

    def visit_crk(self, gate: CRk) -> None:
        self.visit_gate(gate)


def get_circuit_matrix(circuit: Circuit) -> NDArray[np.complex128]:
    """Compute the (large) unitary matrix corresponding to the circuit.

    This matrix has 4**n elements, where n is the number of qubits. Result is stored as a numpy array of complex
    numbers.

    Returns:
        Matrix representation of the circuit.
    """
    impl = _CircuitMatrixCalculator(circuit.qubit_register_size)

    circuit.ir.accept(impl)

    return impl.matrix
