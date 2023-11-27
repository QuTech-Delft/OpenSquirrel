import math
import unittest

import numpy as np

from opensquirrel.circuit import Circuit
from opensquirrel.default_gates import DefaultGates


class TestInterpreterTest(unittest.TestCase):
    def test_hadamard(self):
        circuit = Circuit.from_string(
            DefaultGates,
            r"""
version 3.0
qubit[1] q

h q[0]
""",
        )
        self.assertTrue(
            np.allclose(
                circuit.test_get_circuit_matrix(),
                math.sqrt(0.5)
                * np.array(
                    [
                        [1, 1],
                        [1, -1],
                    ]
                ),
            )
        )

    def test_double_hadamard(self):
        circuit = Circuit.from_string(
            DefaultGates,
            r"""
version 3.0
qubit[1] q

h q[0]
h q[0]
""",
        )
        self.assertTrue(np.allclose(circuit.test_get_circuit_matrix(), np.eye(2)))

    def test_triple_hadamard(self):
        circuit = Circuit.from_string(
            DefaultGates,
            r"""
version 3.0
qubit[1] q

h q[0]
h q[0]
h q[0]
""",
        )
        self.assertTrue(
            np.allclose(
                circuit.test_get_circuit_matrix(),
                math.sqrt(0.5)
                * np.array(
                    [
                        [1, 1],
                        [1, -1],
                    ]
                ),
            )
        )

    def test_hadamard_x(self):
        circuit = Circuit.from_string(
            DefaultGates,
            r"""
version 3.0
qubit[2] q

h q[0]
x q[1]
""",
        )
        self.assertTrue(
            np.allclose(
                circuit.test_get_circuit_matrix(),
                math.sqrt(0.5)
                * np.array(
                    [
                        [0, 0, 1, 1],
                        [0, 0, 1, -1],
                        [1, 1, 0, 0],
                        [1, -1, 0, 0],
                    ]
                ),
            )
        )

    def test_x_hadamard(self):
        circuit = Circuit.from_string(
            DefaultGates,
            r"""
version 3.0
qubit[2] q

h q[1]
x q[0]
""",
        )
        self.assertTrue(
            np.allclose(
                circuit.test_get_circuit_matrix(),
                math.sqrt(0.5)
                * np.array(
                    [
                        [0, 1, 0, 1],
                        [1, 0, 1, 0],
                        [0, 1, 0, -1],
                        [1, 0, -1, 0],
                    ]
                ),
            )
        )

    def test_cnot(self):
        circuit = Circuit.from_string(
            DefaultGates,
            r"""
version 3.0
qubit[2] q

cnot q[1], q[0]
""",
        )

        self.assertTrue(
            np.allclose(
                circuit.test_get_circuit_matrix(),
                np.array(
                    [
                        [1, 0, 0, 0],
                        [0, 1, 0, 0],
                        [0, 0, 0, 1],
                        [0, 0, 1, 0],
                    ]
                ),
            )
        )

    def test_cnot_reversed(self):
        circuit = Circuit.from_string(
            DefaultGates,
            r"""
version 3.0
qubit[2] q

cnot q[0], q[1]
""",
        )

        self.assertTrue(
            np.allclose(
                circuit.test_get_circuit_matrix(),
                np.array(
                    [
                        [1, 0, 0, 0],
                        [0, 0, 0, 1],
                        [0, 0, 1, 0],
                        [0, 1, 0, 0],
                    ]
                ),
            )
        )

    def test_hadamard_cnot(self):
        circuit = Circuit.from_string(
            DefaultGates,
            r"""
version 3.0
qubit[2] q

h q[0]
cnot q[0], q[1]
""",
        )

        self.assertTrue(
            np.allclose(
                circuit.test_get_circuit_matrix(),
                math.sqrt(0.5)
                * np.array(
                    [
                        [1, 1, 0, 0],
                        [0, 0, 1, -1],
                        [0, 0, 1, 1],
                        [1, -1, 0, 0],
                    ]
                ),
            )
        )


if __name__ == "__main__":
    unittest.main()
