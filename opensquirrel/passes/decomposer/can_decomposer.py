import numpy as np
from typing import Tuple

from opensquirrel.ir import Gate, MatrixGate, Can
from opensquirrel.common import ATOL, are_matrices_equivalent_up_to_global_phase
from opensquirrel.utils.matrix_expander import get_matrix, unitary_to_blochsphere
from opensquirrel.utils.math import is_orthogonal, bidiagonalize_unitary_with_special_orthogonals
from opensquirrel.passes.decomposer.general_decomposer import Decomposer

magic_basis = np.asarray(
        [[1, 0, 0, 1j], [0, 1j, 1, 0], [0, 1j, -1, 0], [1, 0, 0, -1j]]
    ) / np.sqrt(2)

magic_basis_h = np.conj(magic_basis.T)
can_gamma = np.array([[1, 1, 1, 1],
                      [1, 1, -1, -1],
                      [-1, 1, -1, 1],
                      [1, -1, -1, 1]]) * 0.25


class CanDecomposer(Decomposer):

    """
       Decomposes 2-qubit controlled unitary gates to K1 + K2 + Can + K3 + K4.
       Applying single-qubit gate fusion after this pass might be beneficial.

       Source of the math: https://threeplusone.com/pubs/on_gates.pdf, chapter 7.2 "Canonical decomposition"
       """
    @staticmethod
    def kron_factor_4x4_to_2x2s(
        matrix: np.ndarray
    ) -> Tuple[complex, np.ndarray, np.ndarray]:
        """Splits a 4x4 matrix U = kron(A, B) into A, B, and a global factor.

        Requires the matrix to be the kronecker product of two 2x2 unitaries.
        Requires the matrix to have a non-zero determinant.

        Args:
            matrix: The 4x4 unitary matrix to factor.

        Returns:
            A scalar factor and a pair of 2x2 unit-determinant matrices. The
            kronecker product of all three is equal to the given matrix.

        Raises:
            ValueError:
                The given matrix can't be tensor-factored into 2x2 pieces.
        """

        # Use the entry with the largest magnitude as a reference point.
        a, b = max(((i, j) for i in range(4) for j in range(4)), key=lambda t: abs(matrix[t]))

        # Extract sub-factors touching the reference cell.
        f1 = np.zeros((2, 2), dtype=np.complex128)
        f2 = np.zeros((2, 2), dtype=np.complex128)
        for i in range(2):
            for j in range(2):
                f1[(a >> 1) ^ i, (b >> 1) ^ j] = matrix[a ^ (i << 1), b ^ (j << 1)]
                f2[(a & 1) ^ i, (b & 1) ^ j] = matrix[a ^ i, b ^ j]

        # Rescale factors to have unit determinants.
        with np.errstate(divide="ignore", invalid="ignore"):
            f1 /= np.sqrt(np.linalg.det(f1)) or 1
            f2 /= np.sqrt(np.linalg.det(f2)) or 1

        # Determine global phase.
        g = matrix[a, b] / (f1[a >> 1, b >> 1] * f2[a & 1, b & 1])
        if np.real(g) < 0:
            f1 *= -1
            g = -g

        if not are_matrices_equivalent_up_to_global_phase(matrix, g * np.kron(f1, f2)):
            raise ValueError("Invalid 4x4 kronecker product.")

        return g, f1, f2

    def so4_to_magic_su2s(
        self,
        mat: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Finds 2x2 special-unitaries A, B where mat = Mag.H @ kron(A, B) @ Mag.

        Mag is the magic basis matrix:

            1  0  0  i
            0  i  1  0
            0  i -1  0     (times sqrt(0.5) to normalize)
            1  0  0 -i

        Args:
            mat: A real 4x4 orthogonal matrix.

        Returns:
            A pair (A, B) of matrices in SU(2) such that Mag.H @ kron(A, B) @ Mag
            is approximately equal to the given matrix.

        Raises:
            ValueError: Bad matrix.
        """

        if mat.shape != (4, 4) or not (is_orthogonal(mat) and (
            mat.shape[0] == 0 or np.allclose(np.linalg.det(mat), 1)
        )):
            raise ValueError('mat must be 4x4 special orthogonal.')

        ab = np.dot(np.dot(magic_basis, mat), magic_basis_h)
        _, a, b = self.kron_factor_4x4_to_2x2s(ab)

        return a, b

    def decompose(self, gate: Gate) -> list[Gate]:

        qubits_in_gate = len(gate.get_qubit_operands())

        if qubits_in_gate != 2:
            return [gate]

        gate_matrix = get_matrix(gate, len(gate.get_qubit_operands()))

        # Starting decomposition

        # Transform input 2-qubit gate to the magic basis
        u_mb = magic_basis_h @ gate_matrix @ magic_basis

        left, d, right = bidiagonalize_unitary_with_special_orthogonals(
            u_mb
        )

        # Recover pieces.
        a1, a0 = self.so4_to_magic_su2s(left.T)
        b1, b0 = self.so4_to_magic_su2s(right.T)
        w, x, y, z = (can_gamma @ np.angle(d).reshape(-1, 1)).flatten()
        g = np.exp(1j * w)

        phase = [complex(1)]  # Accumulated global phase.
        left = [np.eye(2)] * 2  # Per-qubit left factors.
        right = [np.eye(2)] * 2  # Per-qubit right factors.
        v = [x, y, z]  # Remaining XX/YY/ZZ interaction vector.

        # These special-unitary matrices flip the X, Y, and Z axes respectively.
        flippers = [
            np.array([[0, 1], [1, 0]]) * 1j,
            np.array([[0, -1j], [1j, 0]]) * 1j,
            np.array([[1, 0], [0, -1]]) * 1j,
        ]

        # Each of these special-unitary matrices swaps two the roles of two axes.
        # The matrix at index k swaps the *other two* axes (e.g. swappers[1] is a
        # Hadamard operation that swaps X and Z).
        swappers = [
            np.array([[1, -1j], [1j, -1]]) * 1j * np.sqrt(0.5),
            np.array([[1, 1], [1, -1]]) * 1j * np.sqrt(0.5),
            np.array([[0, 1 - 1j], [1 + 1j, 0]]) * 1j * np.sqrt(0.5),
        ]

        # Shifting strength by ½π is equivalent to local ops (e.g. exp(i½π XX)∝XX).
        def shift(k, step):
            v[k] += step * np.pi / 2
            phase[0] *= 1j ** step
            right[0] = np.dot(flippers[k] ** (step % 4), right[0])
            right[1] = np.dot(flippers[k] ** (step % 4), right[1])

        # Two negations is equivalent to temporarily flipping along the other axis.
        def negate(k1_n, k2_n):
            v[k1_n] *= -1
            v[k2_n] *= -1
            phase[0] *= -1
            s = flippers[3 - k1_n - k2_n]  # The other axis' flipper.
            left[1] = np.dot(left[1], s)
            right[1] = np.dot(s, right[1])

        # Swapping components is equivalent to temporarily swapping the two axes.
        def swap(k1_s, k2_s):
            v[k1_s], v[k2_s] = v[k2_s], v[k1_s]
            s = swappers[3 - k1_s - k2_s]  # The other axis' swapper.
            left[0] = np.dot(left[0], s)
            left[1] = np.dot(left[1], s)
            right[0] = np.dot(s, right[0])
            right[1] = np.dot(s, right[1])

        # Shifts an axis strength into the range (-π/4, π/4].
        def canonical_shift(k):
            while v[k] <= -np.pi / 4:
                shift(k, +1)
            while v[k] > np.pi / 4:
                shift(k, -1)

        # Sorts axis strengths into descending order by absolute magnitude.
        def sort():
            if abs(v[0]) < abs(v[1]):
                swap(0, 1)
            if abs(v[1]) < abs(v[2]):
                swap(1, 2)
            if abs(v[0]) < abs(v[1]):
                swap(0, 1)

        # Get all strengths to (-¼π, ¼π] in descending order by absolute magnitude.
        canonical_shift(0)
        canonical_shift(1)
        canonical_shift(2)
        sort()

        # Move all negativity into z.
        if v[0] < 0:
            negate(0, 2)
        if v[1] < 0:
            negate(1, 2)
        canonical_shift(2)

        # If x = π/4, force z to be positive
        if v[0] > np.pi / 4 - ATOL and v[2] < 0:
            shift(0, -1)
            negate(0, 2)

        b1 = np.dot(right[1], b1)
        b0 = np.dot(right[0], b0)
        a1 = np.dot(a1, left[1])
        a0 = np.dot(a0, left[0])
        return [
            unitary_to_blochsphere(b1, gate.get_qubit_operands()[1]),
            unitary_to_blochsphere(b0, gate.get_qubit_operands()[0]),
            Can(gate.get_qubit_operands()[0], gate.get_qubit_operands()[1], v),
            unitary_to_blochsphere(a1, gate.get_qubit_operands()[1]),
            unitary_to_blochsphere(a0, gate.get_qubit_operands()[0])
            ]
