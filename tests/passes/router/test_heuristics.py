from typing import cast

import pytest

from opensquirrel.passes.router.heuristics import DistanceMetric, calculate_distance


@pytest.mark.parametrize(
    ("distance_metric", "expected_distance"),
    [
        (DistanceMetric.MANHATTAN, 3),
        (DistanceMetric.EUCLIDEAN, 5**0.5),
        (DistanceMetric.CHEBYSHEV, 2),
    ],
    ids=["manhattan", "euclidean", "chebyshev"],
)
def test_calculate_distance(distance_metric: DistanceMetric, expected_distance: float) -> None:
    assert calculate_distance(0, 5, 2, distance_metric) == pytest.approx(expected_distance)


def test_calculate_distance_invalid_metric() -> None:
    with pytest.raises(ValueError, match="invalid distance metric"):
        calculate_distance(0, 5, 2, cast("DistanceMetric", "invalid"))
