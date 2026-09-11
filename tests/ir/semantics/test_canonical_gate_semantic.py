import numpy as np
import numpy.testing
import pytest
from numpy.typing import NDArray

from opensquirrel.ir import AxisLike, GateSemantic, IRVisitor, Qubit
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

    @pytest.mark.parametrize("axis", [Qubit(1), [0, [3], [2]], "abc"])
    def test_parse_no_array_like(self, axis: AxisLike) -> None:
        with pytest.raises(TypeError, match="axis requires an ArrayLike"):
            CanonicalAxis(axis)

    @pytest.mark.parametrize(("axis", "size"), [([1, 2], 2), ([1, 2, 3, 4], 4)])
    def test_parse_incorrect_size(self, axis: AxisLike, size: int) -> None:
        with pytest.raises(ValueError, match=f"axis has size {size}: requires an ArrayLike of length 3"):
            CanonicalAxis(axis)

    def test_parse_without_restriction(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(CanonicalAxis, "restrict", False)
        numpy.testing.assert_array_almost_equal(CanonicalAxis((3 / 4, 1 / 4, 0)), [3 / 4, 1 / 4, 0])

    def test_parse_canonical_axis(self) -> None:
        axis = CanonicalAxis((1 / 4, 1 / 4, 0))
        numpy.testing.assert_array_almost_equal(CanonicalAxis(axis), axis)

    def test_accept(self) -> None:
        class Visitor(IRVisitor):
            def visit_canonical_axis(self, axis: CanonicalAxis) -> CanonicalAxis:
                return axis

        axis = CanonicalAxis((0, 0, 0))
        assert axis.accept(Visitor()) is axis

    def test_repr(self) -> None:
        assert repr(CanonicalAxis((1 / 4, 1 / 4, 0))) == "CanonicalAxis[0.25 0.25 0.  ]"


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

    def test_accept(self, semantic: CanonicalGateSemantic) -> None:
        class Visitor(IRVisitor):
            def visit_canonical_gate_semantic(self, canonical: CanonicalGateSemantic) -> CanonicalGateSemantic:
                return canonical

        assert semantic.accept(Visitor()) is semantic

    def test_eq_different_type(self, semantic: CanonicalGateSemantic) -> None:
        assert semantic != CanonicalAxis((0, 0, 0))

    def test_eq_different_axis(self, semantic: CanonicalGateSemantic) -> None:
        assert semantic != CanonicalGateSemantic((1 / 4, 1 / 4, 0))

    def test_eq_without_rotations(self, semantic: CanonicalGateSemantic) -> None:
        assert semantic == CanonicalGateSemantic((0, 0, 0))

    def test_eq_with_rotations(self, semantic_with_rotations: CanonicalGateSemantic) -> None:
        assert semantic_with_rotations == CanonicalGateSemantic((0.25, 0.25, 0.25), semantic_with_rotations.rotations)

    def test_eq_is_symmetric_when_only_one_has_rotations(self, semantic_with_rotations: CanonicalGateSemantic) -> None:
        assert semantic_with_rotations != CanonicalGateSemantic((0.25, 0.25, 0.25))
        assert CanonicalGateSemantic((0.25, 0.25, 0.25)) != semantic_with_rotations

    def test_repr(self, semantic: CanonicalGateSemantic) -> None:
        assert repr(semantic) == "CanonicalGateSemantic(axis=CanonicalAxis[0. 0. 0.])"

    def test_repr_with_rotations(self, semantic_with_rotations: CanonicalGateSemantic) -> None:
        assert repr(semantic_with_rotations).startswith(
            "CanonicalGateSemantic(axis=CanonicalAxis[0.25 0.25 0.25], rotations=["
        )
