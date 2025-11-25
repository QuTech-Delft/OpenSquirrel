from math import pi

import numpy as np

from opensquirrel.ir import (
    Bit,
    Qubit,
)
from opensquirrel.ir.semantics import (
    BlochSphereRotation,
    ControlledGate,
    MatrixGate,
)
from opensquirrel.ir.single_qubit_gate import SingleQubitGate


class TestIR:
    def test_cnot_equality(self) -> None:
        matrix = np.array(
            [
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 0, 1],
                [0, 0, 1, 0],
            ],
        )
        cnot_matrix_gate = MatrixGate(matrix, operands=[4, 100])

        cnot_controlled_gate = ControlledGate(
            4,
            SingleQubitGate(qubit=100, gate_semantic=BlochSphereRotation(axis=(1, 0, 0), angle=pi, phase=pi / 2)),
        )

        assert cnot_controlled_gate == cnot_matrix_gate

    def test_different_qubits_gate(self) -> None:
        matrix = [
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
        ]
        large_identity_matrix_gate = MatrixGate(matrix, operands=[0, 2])
        small_identity_control_gate = ControlledGate(
            4, SingleQubitGate(qubit=2, gate_semantic=BlochSphereRotation(axis=(1, 0, 0), angle=0, phase=0))
        )

        assert large_identity_matrix_gate == small_identity_control_gate

    def test_inverse_gate(self) -> None:
        matrix = [
            [1, 0, 0, 0],
            [0, 0, 0, 1],
            [0, 0, 1, 0],
            [0, 1, 0, 0],
        ]
        inverted_matrix_gate = MatrixGate(matrix, operands=[0, 1])

        inverted_cnot_gate = ControlledGate(
            1,
            SingleQubitGate(qubit=0, gate_semantic=BlochSphereRotation(axis=(1, 0, 0), angle=pi, phase=pi / 2)),
        )

        assert inverted_matrix_gate == inverted_cnot_gate

    def test_global_phase(self) -> None:
        matrix = [
            [1j, 0, 0, 0],
            [0, 0, 0, 1j],
            [0, 0, 1j, 0],
            [0, 1j, 0, 0],
        ]
        inverted_matrix_with_phase = MatrixGate(matrix, operands=[0, 1])

        inverted_cnot_gate = ControlledGate(
            1,
            SingleQubitGate(qubit=0, gate_semantic=BlochSphereRotation(axis=(1, 0, 0), angle=pi, phase=pi / 2)),
        )

        assert inverted_matrix_with_phase == inverted_cnot_gate

    def test_cnot_inequality(self) -> None:
        matrix = [
            [1, 0, 0, 0],
            [0, 0, 1, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1],
        ]
        swap_matrix_gate = MatrixGate(matrix, operands=[4, 100])

        cnot_controlled_gate = ControlledGate(
            4,
            SingleQubitGate(qubit=100, gate_semantic=BlochSphereRotation(axis=(1, 0, 0), angle=pi, phase=pi / 2)),
        )

        assert cnot_controlled_gate != swap_matrix_gate

    def test_hash_difference_bit_qubit(self) -> None:
        assert hash(Qubit(1)) != hash(Bit(1))
