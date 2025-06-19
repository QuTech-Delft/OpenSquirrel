import math
import numpy as np
import functools
from typing import Tuple, List, Callable
from numpy.typing import NDArray, DTypeLike

from opensquirrel.common import ATOL, are_matrices_equivalent_up_to_global_phase
def acos(value: float) -> float:
    """Fix float approximations like 1.0000000000002, which acos does not like."""
    value = max(min(value, 1.0), -1.0)
    return math.acos(value)


def is_orthogonal(matrix: NDArray) -> bool:
    """
    Check if a square matrix is orthogonal.

    A matrix A is orthogonal if A^T * A = I.

    Parameters:
    - matrix: 2D list or NumPy array
    - tol: Tolerance for floating-point errors

    Returns:
    - True if the matrix is orthogonal, False otherwise
    """
    matrix = np.array(matrix)

    if matrix.shape[0] != matrix.shape[1]:  # Must be square
        return False

    identity = np.eye(matrix.shape[0])  # Identity matrix of the same size
    return np.allclose(matrix.T @ matrix, identity, atol=ATOL)  # Check if A^T * A ≈ I

def block_diag(*blocks: np.ndarray) -> np.ndarray:
    """Concatenates blocks into a block diagonal matrix.

    Args:
        *blocks: Square matrices to place along the diagonal of the result.

    Returns:
        A block diagonal matrix with the given blocks along its diagonal.

    Raises:
        ValueError: A block isn't square.
    """
    for b in blocks:
        if b.shape[0] != b.shape[1]:
            raise ValueError('Blocks must be square.')

    if not blocks:
        return np.zeros((0, 0), dtype=np.complex128)

    n = sum(b.shape[0] for b in blocks)

    def _merge_dtypes(dtype1: DTypeLike, dtype2: DTypeLike) -> np.dtype:
        return (np.zeros(0, dtype1) + np.zeros(0, dtype2)).dtype

    dtype = functools.reduce(_merge_dtypes, (b.dtype for b in blocks))

    result = np.zeros(shape=(n, n), dtype=dtype)
    i = 0
    for b in blocks:
        j = i + b.shape[0]
        result[i:j, i:j] = b
        i = j

    return result


def are_axes_consecutive(axis_a_index: int, axis_b_index: int) -> bool:
    """Check if axis 'a' immediately precedes axis 'b' (in a circular fashion [x, y, z, x...])."""
    return axis_a_index - axis_b_index in (-1, 2)


def check_commutation(matrix_a: NDArray, matrix_b: NDArray) -> bool:
    """
    Check if two square matrices A and B commute (i.e., AB = BA).

    Args:
        matrix_a: Matrix A
        matrix_b: Matrix B

    Returns True if they commute, False otherwise.
    """
    matrix_a = np.array(matrix_a)
    matrix_b = np.array(matrix_b)

    if matrix_a.shape != matrix_b.shape or matrix_a.shape[0] != matrix_a.shape[1]:
        raise ValueError("Both matrices must be square and of the same dimensions")

    return are_matrices_equivalent_up_to_global_phase(matrix_a @ matrix_b, matrix_b @ matrix_a)


def is_diagonal(matrix: NDArray) -> bool:
    """
    Check if a given square matrix is diagonal.

    A matrix is diagonal if all off-diagonal elements are zero.
    """
    matrix = np.array(matrix)  # Convert input to NumPy array if not already
    if matrix.shape[0] != matrix.shape[1]:  # Must be square
        return False

    # Check if all off-diagonal elements are zero
    return are_matrices_equivalent_up_to_global_phase(matrix,np.diag(np.diagonal(matrix)))


def is_hermitian(matrix: NDArray) -> bool:
    """
    Check if a given square matrix is Hermitian.

    A matrix is Hermitian if it is equal to its own conjugate transpose.

    Parameters:
    matrix: A square NumPy array

    Returns:
    bool: True if the matrix is Hermitian, False otherwise
    """
    if matrix.shape[0] != matrix.shape[1]:  # Ensure it's square
        return False

    return are_matrices_equivalent_up_to_global_phase(matrix, matrix.conj().T)

def diagonalize_real_symmetric_and_sorted_diagonal_matrices(
    symmetric_matrix: np.ndarray,
    diagonal_matrix: np.ndarray
) -> np.ndarray:
    """Returns an orthogonal matrix that diagonalizes both given matrices.

    The given matrices must commute.
    Guarantees that the sorted diagonal matrix is not permuted by the
    diagonalization (except for nearly-equal values).

    Args:
        symmetric_matrix: A real symmetric matrix.
        diagonal_matrix: A real diagonal matrix with entries along the diagonal
            sorted into descending order.

    Returns:
        An orthogonal matrix P such that P.T @ symmetric_matrix @ P is diagonal
        and P.T @ diagonal_matrix @ P = diagonal_matrix (up to tolerance).

    Raises:
        ValueError: Matrices don't meet preconditions (e.g. not symmetric).
    """

    if np.any(np.imag(symmetric_matrix)) or not is_hermitian(symmetric_matrix):
        raise ValueError('symmetric_matrix must be real symmetric.')
    if (
        not is_diagonal(diagonal_matrix)
        or np.any(np.imag(diagonal_matrix))
        or np.any(diagonal_matrix[:-1, :-1] < diagonal_matrix[1:, 1:])
    ):
        raise ValueError('diagonal_matrix must be real diagonal descending.')
    if not check_commutation(diagonal_matrix, symmetric_matrix):
        raise ValueError('Given matrices must commute.')

    def similar_singular(i, j):
        return np.allclose(diagonal_matrix[i, i], diagonal_matrix[j, j], atol=ATOL)

    # Because the symmetric matrix commutes with the diagonal singulars matrix,
    # the symmetric matrix should be block-diagonal with a block boundary
    # wherever the singular values happen change. So we can use the singular
    # values to extract blocks that can be independently diagonalized.
    def _contiguous_groups(
        length: int, comparator: Callable[[int, int], bool]
    ) -> List[Tuple[int, int]]:
        """Splits range(length) into approximate equivalence classes.

        Args:
            length: The length of the range to split.
            comparator: Determines if two indices have approximately equal items.

        Returns:
            A list of (inclusive_start, exclusive_end) range endpoints. Each
            corresponds to a run of approximately-equivalent items.
        """
        group_result = []
        group_start = 0
        while group_start < length:
            past = group_start + 1
            while past < length and comparator(group_start, past):
                past += 1
            group_result.append((group_start, past))
            group_start = past
        return group_result

    ranges = _contiguous_groups(diagonal_matrix.shape[0], similar_singular)

    p = np.zeros(symmetric_matrix.shape, dtype=np.float64)
    for start, end in ranges:
        block = symmetric_matrix[start:end, start:end]
        _, result = np.linalg.eigh(block)
        p[start:end, start:end] = result

    return p


def bidiagonalize_real_matrix_pair_with_symmetric_products(
    mat1: NDArray,
    mat2: NDArray
) -> Tuple[NDArray, NDArray]:
    """Finds orthogonal matrices that diagonalize both mat1 and mat2.

    Requires mat1 and mat2 to be real.
    Requires mat1.T @ mat2 to be symmetric.
    Requires mat1 @ mat2.T to be symmetric.

    Args:
        mat1: One of the real matrices.
        mat2: The other real matrix.

    Returns:
        A tuple (L, R) of two orthogonal matrices, such that both L @ mat1 @ R
        and L @ mat2 @ R are diagonal matrices.

    Raises:
        ValueError: Matrices don't meet preconditions (e.g. not real).
    """

    def _svd_handling_empty(mat):
        if not mat.shape[0] * mat.shape[1]:
            z = np.zeros((0, 0), dtype=mat.dtype)
            return z, np.array([]), z

        return np.linalg.svd(mat)

    if np.any(np.imag(mat1) != 0):
        raise ValueError('mat1 must be real.')
    if np.any(np.imag(mat2) != 0):
        raise ValueError('mat2 must be real.')
    if not is_hermitian(np.dot(mat1, mat2.T)):
        raise ValueError('mat1 @ mat2.T must be symmetric.')
    if not is_hermitian(np.dot(mat1.T, mat2)):
        raise ValueError('mat1.T @ mat2 must be symmetric.')

    # Use SVD to bi-diagonalize the first matrix.
    base_left, base_diag, base_right = _svd_handling_empty(np.real(mat1))
    base_diag = np.diag(base_diag)


    # Determine where we switch between diagonalization-fixup strategies.
    dim = base_diag.shape[0]
    rank = dim
    while rank > 0 and bool(np.all(np.less_equal(np.abs(base_diag[rank - 1, rank - 1]), ATOL))):
        rank -= 1
    base_diag = base_diag[:rank, :rank]

    # Try diagonalizing the second matrix with the same factors as the first.
    semi_corrected = np.dot(np.dot(base_left.T, np.real(mat2)), base_right.T)

    # Fix up the part of the second matrix's diagonalization that's matched
    # against non-zero diagonal entries in the first matrix's diagonalization
    # by performing simultaneous diagonalization.
    overlap = semi_corrected[:rank, :rank]
    overlap_adjust = diagonalize_real_symmetric_and_sorted_diagonal_matrices(
        overlap, base_diag
    )

    # Fix up the part of the second matrix's diagonalization that's matched
    # against zeros in the first matrix's diagonalization by performing an SVD.
    extra = semi_corrected[rank:, rank:]
    extra_left_adjust, _, extra_right_adjust = _svd_handling_empty(extra)

    # Merge the fixup factors into the initial diagonalization.
    left_adjust = block_diag(overlap_adjust, extra_left_adjust)
    right_adjust = block_diag(overlap_adjust.T, extra_right_adjust)
    left = np.dot(left_adjust.T, base_left.T)
    right = np.dot(base_right.T, right_adjust.T)

    return left, right


def bidiagonalize_unitary_with_special_orthogonals(
    mat: NDArray
) -> Tuple[NDArray, NDArray, NDArray]:
    """Finds orthogonal matrices L, R such that L @ matrix @ R is diagonal.

    Args:
        mat: A unitary matrix.

    Returns:
        A triplet (L, d, R) such that L @ mat @ R = diag(d). Both L and R will
        be orthogonal matrices with determinant equal to 1.

    """

    # Note: Because mat is unitary, setting A = real(mat) and B = imag(mat)
    # guarantees that both A @ B.T and A.T @ B are Hermitian.
    left, right = bidiagonalize_real_matrix_pair_with_symmetric_products(
        np.real(mat), np.imag(mat)
    )

    # Convert to special orthogonal w/o breaking diagonalization.
    with np.errstate(divide="ignore", invalid="ignore"):
        if np.linalg.det(left) < 0:
            left[0, :] *= -1
        if np.linalg.det(right) < 0:
            right[:, 0] *= -1

    diag = np.dot(np.dot(left, mat), right)

    return left, np.diag(diag), right
