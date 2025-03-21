# This module defines basic distance metrics that can be used as heuristics in routing algorithms.

from enum import Enum
from typing import Callable


class DistanceMetric(Enum):
    MANHATTAN = "manhattan"
    EUCLIDEAN = "euclidean"
    CHEBYSHEV = "chebyshev"


def manhattan_distance(a: int, b: int, num_columns: int) -> float:
    """
    Calculate the Manhattan distance between two qubits.

    Args:
        a: The index of the first qubit.
        b: The index of the second qubit.
        num_columns: The number of columns in the grid.

    Returns:
        float: The Manhattan distance between the two qubits.
    """
    x1, y1 = divmod(a, num_columns)
    x2, y2 = divmod(b, num_columns)
    return abs(x1 - x2) + abs(y1 - y2)


def euclidean_distance(a: int, b: int, num_columns: int) -> float:
    """
    Calculate the Euclidean distance between two qubits.

    Args:
        a: The index of the first qubit.
        b: The index of the second qubit.
        num_columns: The number of columns in the grid.

    Returns:
        float: The Euclidean distance between the two qubits.
    """
    x1, y1 = divmod(a, num_columns)
    x2, y2 = divmod(b, num_columns)
    return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5  # type: ignore[no-any-return]


def chebyshev_distance(a: int, b: int, num_columns: int) -> float:
    """
    Calculate the Chebyshev distance between two qubits.

    Args:
        a: The index of the first qubit.
        b: The index of the second qubit.
        num_columns: The number of columns in the grid.

    Returns:
        float: The Chebyshev distance between the two qubits.
    """
    x1, y1 = divmod(a, num_columns)
    x2, y2 = divmod(b, num_columns)
    return max(abs(x1 - x2), abs(y1 - y2))


DISTANCE_FUNCTIONS: dict[DistanceMetric, Callable[[int, int, int], float]] = {
    DistanceMetric.MANHATTAN: manhattan_distance,
    DistanceMetric.EUCLIDEAN: euclidean_distance,
    DistanceMetric.CHEBYSHEV: chebyshev_distance,
}
