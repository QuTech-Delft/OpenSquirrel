from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

import numpy as np
import pytest
from numpy.typing import ArrayLike

from opensquirrel.common import ATOL
from opensquirrel.ir import Axis, BlochSphereRotation, ControlledGate, Expression, MatrixGate, Measure, Qubit


class TestAxis:

    @pytest.fixture(name="axis")
    def axis_fixture(self) -> Axis:
        return Axis(1, 0, 0)

    @pytest.mark.parametrize("expected_class", [Sequence, Expression])
    def test_inheritance(self, axis: Axis, expected_class: type[Any]) -> None:
        assert isinstance(axis, expected_class)

    def test_axis_getter(self, axis: Axis) -> None:
        np.testing.assert_array_equal(axis.value, [1, 0, 0])

    @pytest.mark.parametrize(
        "new_axis, expected_axis",
        [
            ([0, 0, 1], [0, 0, 1]),
            ([0, 3, 4], [0, 3 / 5, 4 / 5]),
            (Axis(0, 1, 0), [0, 1, 0]),
        ],
    )
    def test_axis_setter_no_error(self, axis: Axis, new_axis: ArrayLike, expected_axis: ArrayLike) -> None:
        axis.value = new_axis
        np.testing.assert_array_equal(axis, expected_axis)

    @pytest.mark.parametrize(
        "erroneous_axis, expected_error, expected_error_message",
        [
            (Qubit(1), TypeError, "Axis requires an ArrayLike"),
            ([0, [3], [2]], TypeError, "Axis requires an ArrayLike"),
            (0, ValueError, "Axis requires an ArrayLike of length 3, but received an ArrayLike of length 1."),
            (
                [1, 2, 3, 4],
                ValueError,
                "Axis requires an ArrayLike of length 3, but received an ArrayLike of length 4.",
            ),
        ],
    )
    def test_axis_setter_with_error(
        self, axis: Axis, erroneous_axis: Any, expected_error: type[Exception], expected_error_message: str
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


class TestIR:
    def test_cnot_equality(self) -> None:
        matrix = np.array(
            [
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 0, 1],
                [0, 0, 1, 0],
            ]
        )
        cnot_matrix_gate = MatrixGate(matrix, operands=[Qubit(4), Qubit(100)])

        cnot_controlled_gate = ControlledGate(
            Qubit(4), BlochSphereRotation(qubit=Qubit(100), axis=(1, 0, 0), angle=math.pi, phase=math.pi / 2)
        )

        assert cnot_controlled_gate == cnot_matrix_gate

    def test_different_qubits_gate(self) -> None:
        matrix = np.array(
            [
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1],
            ]
        )
        large_identity_matrix_gate = MatrixGate(matrix, operands=[Qubit(0), Qubit(2)])
        small_identity_control_gate = ControlledGate(
            Qubit(4), BlochSphereRotation(qubit=Qubit(2), axis=(1, 0, 0), angle=0, phase=0)
        )

        assert large_identity_matrix_gate == small_identity_control_gate

    def test_inverse_gate(self) -> None:
        matrix = np.array(
            [
                [1, 0, 0, 0],
                [0, 0, 0, 1],
                [0, 0, 1, 0],
                [0, 1, 0, 0],
            ]
        )
        inverted_matrix_gate = MatrixGate(matrix, operands=[Qubit(0), Qubit(1)])

        inverted_cnot_gate = ControlledGate(
            Qubit(1), BlochSphereRotation(qubit=Qubit(0), axis=(1, 0, 0), angle=math.pi, phase=math.pi / 2)
        )

        assert inverted_matrix_gate == inverted_cnot_gate

    def test_global_phase(self) -> None:
        matrix = np.array(
            [
                [1j, 0, 0, 0],
                [0, 0, 0, 1j],
                [0, 0, 1j, 0],
                [0, 1j, 0, 0],
            ]
        )
        inverted_matrix_with_phase = MatrixGate(matrix, operands=[Qubit(0), Qubit(1)])

        inverted_cnot_gate = ControlledGate(
            Qubit(1), BlochSphereRotation(qubit=Qubit(0), axis=(1, 0, 0), angle=math.pi, phase=math.pi / 2)
        )

        assert inverted_matrix_with_phase == inverted_cnot_gate

    def test_cnot_inequality(self) -> None:
        matrix = np.array(
            [
                [1, 0, 0, 0],
                [0, 0, 1, 0],
                [0, 1, 0, 0],
                [0, 0, 0, 1],
            ]
        )
        swap_matrix_gate = MatrixGate(matrix, operands=[Qubit(4), Qubit(100)])

        cnot_controlled_gate = ControlledGate(
            Qubit(4), BlochSphereRotation(qubit=Qubit(100), axis=(1, 0, 0), angle=math.pi, phase=math.pi / 2)
        )

        assert cnot_controlled_gate != swap_matrix_gate


class TestMeasure:

    @pytest.fixture(name="measure")
    def measure_fixture(self) -> Measure:
        return Measure(Qubit(42), axis=(0, 0, 1))

    def test_repr(self, measure: Measure) -> None:
        expected_repr = "Measure(Qubit[42], axis=Axis[0. 0. 1.])"
        assert repr(measure) == expected_repr

    def test_equality(self, measure: Measure) -> None:
        measure_eq = Measure(Qubit(42), axis=(0, 0, 1))
        assert measure == measure_eq

    @pytest.mark.parametrize(
        "other_measure",
        [Measure(Qubit(43), axis=(0, 0, 1)), Measure(Qubit(42), axis=(1, 0, 0)), "test"],
        ids=["qubit", "axis", "type"],
    )
    def test_inequality(self, measure: Measure, other_measure: Measure | str) -> None:
        assert measure != other_measure

    def test_get_qubit_operands(self, measure: Measure) -> None:
        assert measure.get_qubit_operands() == [Qubit(42)]


class TestBlochSphereRotation:

    @pytest.fixture(name="gate")
    def gate_fixture(self) -> BlochSphereRotation:
        return BlochSphereRotation(qubit=Qubit(42), axis=(1, 0, 0), angle=math.pi, phase=math.tau)

    def test_identity(self) -> None:
        expected_result = BlochSphereRotation(qubit=Qubit(42), axis=(1, 0, 0), angle=0, phase=0)
        assert BlochSphereRotation.identity(Qubit(42)) == expected_result

    @pytest.mark.parametrize(
        "other_gate",
        [
            BlochSphereRotation(qubit=Qubit(42), axis=(1, 0, 0), angle=math.pi, phase=math.tau),
            BlochSphereRotation(qubit=Qubit(42), axis=(1 + ATOL / 2, 0, 0), angle=math.pi, phase=math.tau),
            BlochSphereRotation(qubit=Qubit(42), axis=(1, 0, 0), angle=math.pi + ATOL / 2, phase=math.tau),
            BlochSphereRotation(qubit=Qubit(42), axis=(1, 0, 0), angle=math.pi, phase=math.tau + ATOL / 2),
            BlochSphereRotation(qubit=Qubit(42), axis=(1, 0, 0), angle=math.pi + math.tau, phase=math.tau),
        ],
        ids=["all_equal", "close_axis", "close_angle", "close_phase", "angle+tau"],
    )
    def test_equality(self, gate: BlochSphereRotation, other_gate: BlochSphereRotation) -> None:
        assert gate == other_gate

    @pytest.mark.parametrize(
        "other_gate",
        [
            BlochSphereRotation(qubit=Qubit(43), axis=(1, 0, 0), angle=math.pi, phase=math.tau),
            BlochSphereRotation(qubit=Qubit(42), axis=(0, 1, 0), angle=math.pi, phase=math.tau),
            BlochSphereRotation(qubit=Qubit(42), axis=(1, 0, 0), angle=0, phase=math.tau),
            BlochSphereRotation(qubit=Qubit(42), axis=(1, 0, 0), angle=math.pi, phase=1),
            "test",
        ],
        ids=["qubit", "axis", "angle", "phase", "type"],
    )
    def test_inequality(self, gate: BlochSphereRotation, other_gate: BlochSphereRotation | str) -> None:
        assert gate != other_gate

    def test_get_qubit_operands(self, gate: BlochSphereRotation) -> None:
        assert gate.get_qubit_operands() == [Qubit(42)]

    def test_is_identity(self, gate: BlochSphereRotation) -> None:
        assert BlochSphereRotation.identity(Qubit(42)).is_identity()
        assert not gate.is_identity()


class TestMatrixGate:
    @pytest.fixture(name="gate")
    def gate_fixture(self) -> MatrixGate:
        cnot_matrix = np.array(
            [
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 0, 1],
                [0, 0, 1, 0],
            ]
        )
        cnot_matrix_gate = MatrixGate(cnot_matrix, operands=[Qubit(42), Qubit(100)])
        return cnot_matrix_gate

    def test_repr(self, gate: MatrixGate) -> None:
        assert (
            repr(gate)
            == "MatrixGate(qubits=[Qubit[42], Qubit[100]], matrix=[[1 0 0 0]\n [0 1 0 0]\n [0 0 0 1]\n [0 0 1 0]])"
        )

    def test_get_qubit_operands(self, gate: MatrixGate) -> None:
        assert gate.get_qubit_operands() == [Qubit(42), Qubit(100)]

    def test_is_identity(self, gate: MatrixGate) -> None:
        assert MatrixGate(np.eye(4), operands=[Qubit(42), Qubit(100)]).is_identity()
        assert not gate.is_identity()
