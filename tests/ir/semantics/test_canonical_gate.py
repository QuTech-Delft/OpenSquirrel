import numpy as np
import numpy.testing
import pytest
from numpy.typing import NDArray

from opensquirrel.ir.semantics import CanonicalAxis, CanonicalGate
from opensquirrel.ir.unitary import Gate


class TestCanonicalAxis:
    @pytest.mark.parametrize(
        ("axis", "restricted_axis"),
        [
            (np.array([1, 1, 1], dtype=np.float64), np.array([0, 0, 0], dtype=np.float64)),
            (np.array([-1, -1, -1], dtype=np.float64), np.array([0, 0, 0], dtype=np.float64)),
            (np.array([1, 0, 0], dtype=np.float64), np.array([0, 0, 0], dtype=np.float64)),
            (np.array([3 / 4, 1 / 4, 0], dtype=np.float64), np.array([1 / 4, 1 / 4, 0], dtype=np.float64)),
            (np.array([5 / 8, 3 / 8, 0], dtype=np.float64), np.array([3 / 8, 3 / 8, 0], dtype=np.float64)),
            (np.array([3 / 4, 3 / 4, 3 / 4], dtype=np.float64), np.array([1 / 4, 1 / 4, 1 / 4], dtype=np.float64)),
            (np.array([1 / 2, 3 / 4, 3 / 4], dtype=np.float64), np.array([1 / 2, 1 / 4, 1 / 4], dtype=np.float64)),
            (np.array([64 / 2, 32 / 4, 33 / 4], dtype=np.float64), np.array([1 / 4, 0, 0], dtype=np.float64)),
        ],
    )
    def test_restrict_to_weyl_chamber(self, axis: NDArray[np.float64], restricted_axis: NDArray[np.float64]) -> None:
        numpy.testing.assert_array_almost_equal(CanonicalAxis.restrict_to_weyl_chamber(axis), restricted_axis)


class TestCanonicalGate:
    @pytest.fixture
    def gate(self) -> CanonicalGate:
        return CanonicalGate(0, 1, (0, 0, 0))

    def test_eq(self, gate: CanonicalGate) -> None:
        assert gate.is_identity()

    def test_init(self, gate: CanonicalGate) -> None:
        assert isinstance(gate, Gate)
        assert hasattr(gate, "axis")
        assert isinstance(gate.axis, CanonicalAxis)
        with pytest.raises(ValueError, match="control and target qubit cannot be the same"):
            CanonicalGate(0, 0, (0, 0, 0))
