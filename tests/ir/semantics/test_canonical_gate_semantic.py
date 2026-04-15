import numpy as np
import numpy.testing
import pytest
from numpy.typing import NDArray

from opensquirrel.ir import GateSemantic
from opensquirrel.ir.semantics import BlochSphereRotation, CanonicalAxis, CanonicalGateSemantic


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


class TestCanonicalGateSemantic:
    @pytest.fixture
    def semantic(self) -> CanonicalGateSemantic:
        return CanonicalGateSemantic((0, 0, 0))

    @pytest.fixture
    def semantic_with_rotations(self) -> CanonicalGateSemantic:
        """Fixture for a CanonicalGateSemantic with rotations."""
        rotations = [
            BlochSphereRotation(axis=(1, 0, 0), angle=0.5, phase=0.1),
            BlochSphereRotation(axis=(0, 1, 0), angle=1.0, phase=0.2),
            BlochSphereRotation(axis=(0, 0, 1), angle=1.5, phase=0.3),
            BlochSphereRotation(axis=(1, 0, 0), angle=0.75, phase=0.4),
        ]
        return CanonicalGateSemantic((0.25, 0.25, 0.25), rotations)

    def test_init(self, semantic: CanonicalGateSemantic) -> None:
        assert isinstance(semantic, GateSemantic)
        assert hasattr(semantic, "axis")
        assert isinstance(semantic.axis, CanonicalAxis)

    def test_is_identity_with_zero_axis(self, semantic: CanonicalGateSemantic) -> None:
        assert semantic.is_identity()

    def test_is_identity_with_non_zero_axis(self, semantic_with_rotations: CanonicalGateSemantic) -> None:
        assert not semantic_with_rotations.is_identity()

    def test_rotations_attribute_list(self, semantic_with_rotations: CanonicalGateSemantic) -> None:
        assert semantic_with_rotations.rotations is not None
        assert len(semantic_with_rotations.rotations) == 4
        assert all(isinstance(rot, BlochSphereRotation) for rot in semantic_with_rotations.rotations)

    def test_invalid_number_of_rotations(self) -> None:
        rotations = [BlochSphereRotation(axis=(1, 0, 0), angle=0.5, phase=0.1)]
        with pytest.raises(ValueError, match="invalid number of rotations, expected 4 but got 1"):
            CanonicalGateSemantic((0, 0, 0), rotations)
