import unittest

import numpy as np

from opensquirrel.default_gates import *


class SquirrelIRTest(unittest.TestCase):
    def test_cnot_equality(self):
        cnot_matrix_gate = MatrixGate(
            np.array(
                [
                    [1, 0, 0, 0],
                    [0, 1, 0, 0],
                    [0, 0, 0, 1],
                    [0, 0, 1, 0],
                ]
            ),
            operands=[Qubit(4), Qubit(100)],
        )

        cnot_controlled_gate = ControlledGate(
            Qubit(4), BlochSphereRotation(qubit=Qubit(100), axis=(1, 0, 0), angle=math.pi, phase=math.pi / 2)
        )

        self.assertTrue(cnot_controlled_gate == cnot_matrix_gate)

    def test_cnot_inequality(self):
        swap_matrix_gate = MatrixGate(
            np.array(
                [
                    [1, 0, 0, 0],
                    [0, 0, 1, 0],
                    [0, 1, 0, 0],
                    [0, 0, 0, 1],
                ]
            ),
            operands=[Qubit(4), Qubit(100)],
        )

        cnot_controlled_gate = ControlledGate(
            Qubit(4), BlochSphereRotation(qubit=Qubit(100), axis=(1, 0, 0), angle=math.pi, phase=math.pi / 2)
        )

        self.assertFalse(cnot_controlled_gate == swap_matrix_gate)

    def test_different_qubits_gate(self):
        large_identity_matrix_gate = MatrixGate(
            np.array(
                [
                    [1, 0, 0, 0],
                    [0, 1, 0, 0],
                    [0, 0, 1, 0],
                    [0, 0, 0, 1],
                ]
            ),
            operands=[Qubit(0), Qubit(2)],
        )
        small_identity_control_gate = ControlledGate(
            Qubit(4), BlochSphereRotation(qubit=Qubit(2), axis=(1, 0, 0), angle=0, phase=0)
        )

        self.assertTrue(large_identity_matrix_gate == small_identity_control_gate)

    def test_inverse_gate(self):
        inverted_matrix_gate = MatrixGate(
            np.array(
                [
                    [1, 0, 0, 0],
                    [0, 0, 0, 1],
                    [0, 0, 1, 0],
                    [0, 1, 0, 0],
                ]
            ),
            operands=[Qubit(0), Qubit(1)],
        )

        inverted_cnot_gate = ControlledGate(
            Qubit(1), BlochSphereRotation(qubit=Qubit(0), axis=(1, 0, 0), angle=math.pi, phase=math.pi / 2)
        )

        self.assertTrue(inverted_matrix_gate == inverted_cnot_gate)

    def test_global_phase(self):
        inverted_matrix_with_phase = MatrixGate(
            np.array(
                [
                    [1j, 0, 0, 0],
                    [0, 0, 0, 1j],
                    [0, 0, 1j, 0],
                    [0, 1j, 0, 0],
                ]
            ),
            operands=[Qubit(0), Qubit(1)],
        )

        inverted_cnot_gate = ControlledGate(
            Qubit(1), BlochSphereRotation(qubit=Qubit(0), axis=(1, 0, 0), angle=math.pi, phase=math.pi / 2)
        )

        self.assertTrue(inverted_matrix_with_phase == inverted_cnot_gate)
