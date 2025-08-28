from collections.abc import Sequence
from typing import Any, SupportsInt

import numpy as np
import pytest
from numpy.typing import NDArray

from opensquirrel.ir import Axis, AxisLike, Bit, Float, Int, Qubit
from opensquirrel.ir.expression import Expression


class TestFloat:
    def test_type_error(self) -> None:
        with pytest.raises(TypeError, match="value must be a float"):
            Float("f")  # type: ignore

    def test_init(self) -> None:
        assert Float(1).value == 1.0


class TestInt:
    @pytest.mark.parametrize("value", ["f", None, {1}])
    def test_type_error(self, value: Any) -> None:
        with pytest.raises(TypeError, match="value must be an int"):
            Int(value)

    @pytest.mark.parametrize("value", [1, 1.0, 1.1, Int(1)])
    def test_init(self, value: SupportsInt) -> None:
        assert Int(value).value == 1


class TestBit:
    def test_type_error(self) -> None:
        with pytest.raises(TypeError, match="index must be a BitLike"):
            Bit("f")  # type: ignore

    def test_init(self) -> None:
        assert str(Bit(1)) == "Bit[1]"


class TestQubit:
    def test_type_error(self) -> None:
        with pytest.raises(TypeError, match="index must be a QubitLike"):
            Qubit("f")  # type: ignore

    def test_init(self) -> None:
        assert str(Qubit(1)) == "Qubit[1]"


class TestAxis:
    @pytest.fixture
    def axis(self) -> Axis:
        return Axis(1, 0, 0)

    @pytest.mark.parametrize("expected_class", [Sequence, Expression])
    def test_inheritance(self, axis: Axis, expected_class: type[Any]) -> None:
        assert isinstance(axis, expected_class)

    def test_axis_getter(self, axis: Axis) -> None:
        np.testing.assert_array_equal(axis.value, [1, 0, 0])

    @pytest.mark.parametrize(
        ("new_axis", "expected_axis"),
        [
            ([0, 0, 1], [0, 0, 1]),
            ([0, 3, 4], [0, 3 / 5, 4 / 5]),
            (Axis(0, 1, 0), [0, 1, 0]),
        ],
    )
    def test_axis_setter_no_error(self, axis: Axis, new_axis: AxisLike, expected_axis: list[float]) -> None:
        axis.value = new_axis
        np.testing.assert_array_equal(axis, expected_axis)

    @pytest.mark.parametrize(
        ("erroneous_axis", "expected_error", "expected_error_message"),
        [
            (Qubit(1), TypeError, "axis requires an ArrayLike"),
            ([0, [3], [2]], TypeError, "axis requires an ArrayLike"),
            (0, ValueError, "axis requires an ArrayLike of length 3, but received an ArrayLike of length 1"),
            (
                [1, 2, 3, 4],
                ValueError,
                "axis requires an ArrayLike of length 3, but received an ArrayLike of length 4",
            ),
            ([0, 0, 0], ValueError, "axis requires at least one element to be non-zero"),
        ],
    )
    def test_axis_setter_with_error(
        self,
        axis: Axis,
        erroneous_axis: Any,
        expected_error: type[Exception],
        expected_error_message: str,
    ) -> None:
        with pytest.raises(expected_error, match=expected_error_message):
            axis.value = erroneous_axis

    def test_get_item(self, axis: Axis) -> None:
        assert axis[0] == 1
        assert axis[1] == 0
        assert axis[2] == 0

    def test_len(self, axis: Axis) -> None:
        assert len(axis) == 3

    def test_repr(self, axis: Axis) -> None:
        assert repr(axis) == "Axis[1. 0. 0.]"

    def test_array(self, axis: Axis) -> None:
        np.testing.assert_array_equal(axis, [1, 0, 0])

    @pytest.mark.parametrize("other", [Axis(1, 0, 0), Axis([1, 0, 0]), Axis([[1], [0], [0]])])
    def test_eq_true(self, axis: Axis, other: Any) -> None:
        assert axis == other

    @pytest.mark.parametrize("other", ["test", Axis(0, 1, 0)])
    def test_eq_false(self, axis: Axis, other: Any) -> None:
        assert axis != other

    @pytest.mark.parametrize(
        ("axis", "expected"),
        [
            ([1, 0, 0], np.array([1, 0, 0], dtype=np.float64)),
            ([0, 0, 0], ValueError),
            ([1, 2], ValueError),
            ([1, 2, 3, 4], ValueError),
            ([0, 1, 0], np.array([0, 1, 0], dtype=np.float64)),
            (["a", "b", "c"], TypeError),
        ],
    )
    def test_constructor(self, axis: AxisLike, expected: Any) -> None:
        if isinstance(expected, type) and issubclass(expected, Exception):
            with pytest.raises(expected):
                Axis(axis)
        else:
            assert isinstance(expected, np.ndarray)
            obj = Axis(axis)
            np.testing.assert_array_equal(obj.value, expected)

    @pytest.mark.parametrize(
        ("axis", "expected"),
        [
            ([1, 0, 0], np.array([1, 0, 0], dtype=np.float64)),
            ([0, 0, 0], ValueError),
            ([1, 2], ValueError),
            ([1, 2, 3, 4], ValueError),
            ([0, 1, 0], np.array([0, 1, 0], dtype=np.float64)),
            (["a", "b", "c"], TypeError),
        ],
    )
    def test_parse(self, axis: AxisLike, expected: Any) -> None:
        if isinstance(expected, type) and issubclass(expected, Exception):
            with pytest.raises(expected):
                Axis.parse(axis)
        else:
            assert isinstance(expected, np.ndarray)
            obj = Axis.parse(axis)
            np.testing.assert_array_equal(obj, expected)

    @pytest.mark.parametrize(
        ("axis", "expected"),
        [
            (np.array([1, 0, 0], dtype=np.float64), np.array([1, 0, 0], dtype=np.float64)),
            (np.array([0, 1, 0], dtype=np.float64), np.array([0, 1, 0], dtype=np.float64)),
            (np.array([0, 0, 1], dtype=np.float64), np.array([0, 0, 1], dtype=np.float64)),
            (
                np.array([1, 1, 1], dtype=np.float64),
                np.array([1 / np.sqrt(3), 1 / np.sqrt(3), 1 / np.sqrt(3)], dtype=np.float64),
            ),
        ],
    )
    def test_normalize(self, axis: AxisLike, expected: NDArray[np.float64]) -> None:
        obj = Axis.normalize(np.array(axis, dtype=np.float64))
        assert isinstance(expected, np.ndarray)
        np.testing.assert_array_almost_equal(obj, expected)
