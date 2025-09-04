from __future__ import annotations

from collections.abc import Sequence
from math import pi, tau
from typing import Any

import numpy as np
import pytest
from numpy.typing import NDArray

from opensquirrel import (
    X90,
    H,
    I,
    MinusX90,
    Rn,
    Rx,
    Ry,
    Rz,
    TDagger,
    X,
)
from opensquirrel.common import ATOL
from opensquirrel.ir import (
    Axis,
    AxisLike,
    Qubit,
)
from opensquirrel.ir.expression import Expression
from opensquirrel.ir.semantics import BlochSphereRotation


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
        obj = Axis(np.array(axis, dtype=np.float64))
        assert isinstance(expected, np.ndarray)
        np.testing.assert_array_almost_equal(np.array(obj), expected)


class TestBlochSphereRotation:
    @pytest.fixture
    def gate(self) -> BlochSphereRotation:
        return BlochSphereRotation(qubit=42, axis=(1, 0, 0), angle=pi, phase=tau)

    @pytest.mark.parametrize(
        "other_gate",
        [
            BlochSphereRotation(qubit=42, axis=(1, 0, 0), angle=pi, phase=tau),
            BlochSphereRotation(qubit=42, axis=(1 + ATOL / 2, 0, 0), angle=pi, phase=tau),
            BlochSphereRotation(qubit=42, axis=(1, 0, 0), angle=pi + ATOL / 2, phase=tau),
            BlochSphereRotation(qubit=42, axis=(1, 0, 0), angle=pi, phase=tau + ATOL / 2),
            BlochSphereRotation(qubit=42, axis=(1, 0, 0), angle=pi + tau, phase=tau),
        ],
        ids=["all_equal", "close_axis", "close_angle", "close_phase", "angle+tau"],
    )
    def test_equality(self, gate: BlochSphereRotation, other_gate: BlochSphereRotation) -> None:
        assert gate == other_gate

    @pytest.mark.parametrize(
        "other_gate",
        [
            BlochSphereRotation(qubit=43, axis=(1, 0, 0), angle=pi, phase=tau),
            BlochSphereRotation(qubit=42, axis=(0, 1, 0), angle=pi, phase=tau),
            BlochSphereRotation(qubit=42, axis=(1, 0, 0), angle=0, phase=tau),
            BlochSphereRotation(qubit=42, axis=(1, 0, 0), angle=pi, phase=1),
            "test",
        ],
        ids=["qubit", "axis", "angle", "phase", "type"],
    )
    def test_inequality(self, gate: BlochSphereRotation, other_gate: BlochSphereRotation | str) -> None:
        assert gate != other_gate

    def test_get_qubit_operands(self, gate: BlochSphereRotation) -> None:
        assert gate.get_qubit_operands() == [Qubit(42)]

    def test_is_identity(self, gate: BlochSphereRotation) -> None:
        assert I(42).is_identity()
        assert not gate.is_identity()

    @pytest.mark.parametrize(
        ("bsr", "default_gate"),
        [
            (BlochSphereRotation(qubit=0, axis=(1, 0, 1), angle=pi, phase=pi / 2), H(0)),
            (BlochSphereRotation(qubit=0, axis=(1, 0, 0), angle=pi, phase=pi / 2), X(0)),
            (BlochSphereRotation(qubit=0, axis=(1, 0, 0), angle=pi / 2, phase=pi / 4), X90(0)),
            (BlochSphereRotation(qubit=0, axis=(-1, 0, 0), angle=-pi / 2, phase=-pi / 4), X90(0)),
            (BlochSphereRotation(qubit=0, axis=(1, 0, 0), angle=-pi / 2, phase=-pi / 4), MinusX90(0)),
            (BlochSphereRotation(qubit=0, axis=(-1, 0, 0), angle=pi / 2, phase=pi / 4), MinusX90(0)),
            (BlochSphereRotation(qubit=0, axis=(0, 0, 1), angle=-pi / 4, phase=-pi / 8), TDagger(0)),
            (BlochSphereRotation(qubit=0, axis=(1, 0, 0), angle=pi / 4, phase=0), Rx(0, pi / 4)),
            (BlochSphereRotation(qubit=0, axis=(0, 1, 0), angle=pi / 3, phase=0), Ry(0, pi / 3)),
            (BlochSphereRotation(qubit=0, axis=(0, 0, 1), angle=3 * pi / 4, phase=0), Rz(0, 3 * pi / 4)),
            (BlochSphereRotation(qubit=0, axis=(1, 0, 1), angle=pi, phase=0), Rn(0, 1, 0, 1, pi, 0)),
        ],
        ids=["H", "X", "X90-1", "X90-2", "mX90-1", "mX90-2", "Tdag", "Rx", "Ry", "Rz", "Rn"],
    )
    def test_default_gate_matching(self, bsr: BlochSphereRotation, default_gate: BlochSphereRotation) -> None:
        matched_bsr = BlochSphereRotation.try_match_replace_with_default(bsr)
        assert matched_bsr == default_gate
        assert matched_bsr.name == default_gate.name
