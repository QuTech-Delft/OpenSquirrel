from __future__ import annotations

import math

import numpy as np
import pytest
from numpy.typing import NDArray

from opensquirrel.common import ATOL
from opensquirrel.ir import BlochSphereRotation, ControlledGate, MatrixGate, Measure, Qubit


class TestIR:
    def test_cnot_equality(self):
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

    def test_different_qubits_gate(self):
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

    def test_inverse_gate(self):
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

    def test_global_phase(self):
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

    def test_cnot_inequality(self):
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
        expected_repr = "Measure(Qubit[42], axis=[0. 0. 1.])"
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

    def test_is_identity(self, gate: BlochSphereRotation) -> bool:
        assert BlochSphereRotation.identity(42).is_identity()
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

    def test_repr(self, gate: MatrixGate):
        assert (
            repr(gate)
            == "MatrixGate(qubits=[Qubit[42], Qubit[100]], matrix=[[1 0 0 0]\n [0 1 0 0]\n [0 0 0 1]\n [0 0 1 0]])"
        )

    def test_get_qubit_operands(self, gate: MatrixGate) -> None:
        assert gate.get_qubit_operands() == [Qubit(42), Qubit(100)]

    def test_is_identity(self, gate: MatrixGate) -> None:
        assert MatrixGate(np.eye(4), operands=[Qubit(42), Qubit(100)]).is_identity()
        assert not gate.is_identity()
