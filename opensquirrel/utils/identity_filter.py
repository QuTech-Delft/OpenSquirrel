from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import ArrayLike

from opensquirrel.common import ATOL

if TYPE_CHECKING:
    from opensquirrel.ir import Gate


def filter_out_identities(gates: Iterable[Gate]) -> list[Gate]:
    return [gate for gate in gates if not gate.is_identity()]


def is_identity_matrix(matrix: ArrayLike) -> bool:
    norm_matrix = np.abs(matrix)
    return np.allclose(norm_matrix, np.eye(norm_matrix.shape[0]), atol=ATOL)
