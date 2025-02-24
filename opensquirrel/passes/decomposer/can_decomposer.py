from __future__ import annotations

import math
from abc import ABC, abstractmethod
import numpy as np
import itertools
import scipy
from collections.abc import Callable
from typing import Any, ClassVar

from opensquirrel import Rx, Ry, Rz
from opensquirrel.common import ATOL
from opensquirrel.ir import Axis, AxisLike, BlochSphereRotation, Gate
from opensquirrel.passes.decomposer.general_decomposer import Decomposer
from opensquirrel.utils import get_matrix
from opensquirrel.utils import acos, are_axes_consecutive, filter_out_identities


class CanDecomposer(Decomposer, ABC):

    def __init__(self) -> None:

    def decompose(self, g: Gate) -> list[Gate]:
        """

        """
        # Canonical to magic basis matrix mapping
        Q = np.asarray(
            [[1, 0, 0, 1j], [0, 1j, 1, 0], [0, 1j, -1, 0], [1, 0, 0, -1j]]
        ) / np.sqrt(2)
        # Q dagger
        Q_H = Q.conj().T

        U = get_matrix(g, len(g.get_qubit_operands()))

        U_mb = Q_H @ U @ Q
        # Find matrix M = Q^T * Q. This matrix will be used to extract the eigenvalues of the canonical gate
        # in the magic basis as well as the tensor product of the single-qubit operations before and after
        # the application of the canonical gate.
        M = U_mb.transpose() @ U_mb

        # Decompose the matrix M using an orthogonal eigenvector basis.
        for i in range(M.shape[0] * M.shape[1]):
            c = np.random.uniform(0, 1)
            auxM = c * M.real + (1 - c) * M.imag
            _, eigvecs = np.linalg.eigh(auxM)
            eigvecs = np.array(eigvecs, dtype=complex)
            eigvals = np.diag(eigvecs.transpose() @ M @ eigvecs)

            reconstructed = eigvecs @ np.diag(eigvals) @ eigvecs.transpose()
            if np.allclose(M, reconstructed):
                break

        # Use the eigenvalues of the matrix M to determine the coordinates of the canonical gate.
        lambdas = np.sqrt(eigvals)
        try:
            for permutation in itertools.permutations(range(4)):
                for signs in ([1, 1, 1, 1], [1, 1, -1, -1], [-1, 1, -1, 1], [1, -1, -1, 1]):
                    signed_lambdas = lambdas * np.asarray(signs)
                    perm = list(permutation)
                    lambdas_perm = signed_lambdas[perm]

                    l1, l2, l3, l4 = lambdas_perm
                    tx = np.real(1j / 4 * np.log(l1 * l2 / (l3 * l4))) / np.pi
                    ty = np.real(1j / 4 * np.log(l2 * l4 / (l1 * l3))) / np.pi
                    tz = np.real(1j / 4 * np.log(l1 * l4 / (l2 * l3))) / np.pi

                    coords = np.asarray([tx, ty, tz])
                    coords[np.abs(coords - 1) < ATOL] = -1
                    if all(coords < 0):
                        coords += 1
                    if np.abs(coords[0] - coords[1]) < ATOL:
                        coords[1] = coords[0]
                    if np.abs(coords[1] - coords[2]) < ATOL:
                        coords[2] = coords[1]
                    if np.abs(coords[0] - coords[1] - 1 / 2) < ATOL:
                        coords[1] = coords[0] - 1 / 2
                    coords[np.abs(coords) < ATOL] = 0

                    tx, ty, tz = coords

                    # Check whether coordinates are inside the Weyl Chamber
                    if (1 / 2 >= tx >= ty >= tz >= 0) or (1 / 2 >= (1 - tx) >= ty >= tz > 0):
                        print('pass')
                        raise StopIteration

        except StopIteration:
            pass

        lambdas = (lambdas * signs)[perm]
        O2 = (np.diag(signs) @ eigvecs.transpose())[perm]
        F = np.diag(lambdas)
        O1 = U_mb @ O2.transpose() @ F.conj()

        neg = np.diag([-1, 1, 1, 1])
        if np.linalg.det(O2) < 0:
            O2 = neg @ O2
            O1 = O1 @ neg

        K1 = Q @ O1 @ Q_H
        A = Q @ F @ Q_H
        K2 = Q @ O2 @ Q_H

        U_decomp = K1 @ A @ K2

        Can = scipy.linalg.expm(-1j * np.pi * (tx * XX + ty * YY + tz * ZZ))
