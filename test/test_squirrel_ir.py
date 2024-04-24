from __future__ import annotations

import math

import numpy as np
import pytest

from opensquirrel.squirrel_ir import BlochSphereRotation, ControlledGate, MatrixGate, Measure, Qubit


class TestSquirrelIR:
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

    def test_repr_dunder(self, measure: Measure) -> None:
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

    @pytest.mark.parametrize(
        "mapping, expected_output",
        [({42: 42}, Measure(Qubit(42), axis=(0, 0, 1))), ({42: 0}, Measure(Qubit(0), axis=(0, 0, 1)))],
    )
    def test_relabel(self, measure: Measure, mapping: dict[int, int], expected_output: Measure) -> None:
        measure.relabel(mapping)
        assert measure == expected_output
