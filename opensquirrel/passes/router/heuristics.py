# This module defines basic distance metrics that can be used as heuristics in routing algorithms.

from enum import Enum


class DistanceMetric(Enum):
    MANHATTAN = "manhattan"
    EUCLIDEAN = "euclidean"
    CHEBYSHEV = "chebyshev"


def calculate_distance(q0_index: int, q1_index: int, num_columns: int, distance_metric: DistanceMetric) -> float:
    """
    Calculate the distance between two qubits based on the specified distance metric.
    Args:
        q0_index (int): The index of the first qubit.
        q1_index (int): The index of the second qubit.
        num_columns (int): The number of columns in the grid.
        distance_metric (DistanceMetric): Distance metric to be used (Manhattan, Euclidean, or Chebyshev).
    Returns:
        float: The distance between the two qubits.
    """
    x1, y1 = divmod(q0_index, num_columns)
    x2, y2 = divmod(q1_index, num_columns)

    if distance_metric == DistanceMetric.MANHATTAN:
        return abs(x1 - x2) + abs(y1 - y2)
    if distance_metric == DistanceMetric.EUCLIDEAN:
        return float(((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5)
    if distance_metric == DistanceMetric.CHEBYSHEV:
        return max(abs(x1 - x2), abs(y1 - y2))
    return None
