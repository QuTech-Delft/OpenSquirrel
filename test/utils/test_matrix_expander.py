import math
import unittest

import numpy as np

from opensquirrel.squirrel_ir import BlochSphereRotation, ControlledGate, MatrixGate, Qubit
from opensquirrel.utils import matrix_expander


class MatrixExpanderTest(unittest.TestCase):
    def test_bloch_sphere_rotation(self):
        gate = BlochSphereRotation(qubit=Qubit(0), axis=(0.8, -0.3, 1.5), angle=0.9468, phase=2.533)
        self.assertTrue(
            np.allclose(
                matrix_expander.get_matrix(gate, 2),
                np.array(
                    [
                        [-0.50373461 + 0.83386635j, 0.05578802 + 0.21864595j, 0, 0],
                        [0.18579927 + 0.12805072j, -0.95671077 + 0.18381011j, 0, 0],
                        [0, 0, -0.50373461 + 0.83386635j, 0.05578802 + 0.21864595j],
                        [0, 0, 0.18579927 + 0.12805072j, -0.95671077 + 0.18381011j],
                    ]
                ),
            )
        )

    def test_controlled_gate(self):
        gate = ControlledGate(
            Qubit(2), BlochSphereRotation(qubit=Qubit(0), axis=(1, 0, 0), angle=math.pi, phase=math.pi / 2)
        )
        self.assertTrue(
            np.allclose(
                matrix_expander.get_matrix(gate, 3),
                np.array(
                    [
                        [1, 0, 0, 0, 0, 0, 0, 0],
                        [0, 1, 0, 0, 0, 0, 0, 0],
                        [0, 0, 1, 0, 0, 0, 0, 0],
                        [0, 0, 0, 1, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 1, 0, 0],
                        [0, 0, 0, 0, 1, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 1],
                        [0, 0, 0, 0, 0, 0, 1, 0],
                    ]
                ),
            )
        )

    def test_matrix_gate(self):
        gate = MatrixGate(
            np.array(
                [
                    [1, 0, 0, 0],
                    [0, 0, 1, 0],
                    [0, 1, 0, 0],
                    [0, 0, 0, 1],
                ]
            ),
            operands=[Qubit(1), Qubit(2)],
        )
        self.assertTrue(
            np.allclose(
                matrix_expander.get_matrix(gate, 3),
                np.array(
                    [
                        [1, 0, 0, 0, 0, 0, 0, 0],
                        [0, 1, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 1, 0, 0, 0],
                        [0, 0, 0, 0, 0, 1, 0, 0],
                        [0, 0, 1, 0, 0, 0, 0, 0],
                        [0, 0, 0, 1, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 1, 0],
                        [0, 0, 0, 0, 0, 0, 0, 1],
                    ]
                ),
            )
        )
