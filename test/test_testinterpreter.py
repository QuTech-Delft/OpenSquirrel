from src.Circuit import Circuit
from test.TestGates import TEST_GATES
import unittest
import numpy as np
import math

class TestInterpreterTest(unittest.TestCase):
    def test_hadamard(self):
        circuit = Circuit(TEST_GATES, r"""
version 3.0
qubit[1] q

h q[0]
""")
        self.assertTrue(np.allclose(circuit.test_get_circuit_matrix(), math.sqrt(.5) * np.array([
                [1, 1],
                [1, -1],
        ])))
    
    def test_doublehadamard(self):
        circuit = Circuit(TEST_GATES, r"""
version 3.0
qubit[1] q

h q[0]
h q[0]
""")
        self.assertTrue(np.allclose(circuit.test_get_circuit_matrix(), np.eye(2)))

    def test_triplehadamard(self):
        circuit = Circuit(TEST_GATES, r"""
version 3.0
qubit[1] q

h q[0]
h q[0]
h q[0]
""")
        self.assertTrue(np.allclose(circuit.test_get_circuit_matrix(), math.sqrt(.5) * np.array([
                [1, 1],
                [1, -1],
        ])))

    def test_hadamardx(self):
        circuit = Circuit(TEST_GATES, r"""
version 3.0
qubit[2] q

h q[0]
x q[1]
""")
        self.assertTrue(np.allclose(circuit.test_get_circuit_matrix(), math.sqrt(.5) * np.array([
                [0, 0, 1, 1],
                [0, 0, 1, -1],
                [1, 1, 0, 0],
                [1, -1, 0, 0],
        ])))

    def test_xhadamard(self):
        circuit = Circuit(TEST_GATES, r"""
version 3.0
qubit[2] q

h q[1]
x q[0]
""")
        self.assertTrue(np.allclose(circuit.test_get_circuit_matrix(), math.sqrt(.5) * np.array([
                [0, 1, 0, 1],
                [1, 0, 1, 0],
                [0, 1, 0, -1],
                [1, 0, -1, 0],
        ])))

    def test_cnot(self):
        circuit = Circuit(TEST_GATES, r"""
version 3.0
qubit[2] q

cnot q[1], q[0]
""")

        self.assertTrue(np.allclose(circuit.test_get_circuit_matrix(), np.array([
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 0, 1],
                [0, 0, 1, 0],
        ])))

    def test_cnot_reversed(self):
        circuit = Circuit(TEST_GATES, r"""
version 3.0
qubit[2] q

cnot q[0], q[1]
""")

        self.assertTrue(np.allclose(circuit.test_get_circuit_matrix(), np.array([
                [1, 0, 0, 0],
                [0, 0, 0, 1],
                [0, 0, 1, 0],
                [0, 1, 0, 0],
        ])))

    def test_hadamard_cnot(self):
        circuit = Circuit(TEST_GATES, r"""
version 3.0
qubit[2] q

h q[0]
cnot q[0], q[1]
""")

        self.assertTrue(np.allclose(circuit.test_get_circuit_matrix(), math.sqrt(.5) * np.array([
                [1, 1, 0, 0],
                [0, 0, 1, -1],
                [0, 0, 1, 1],
                [1, -1, 0, 0],
        ])))


if __name__ == '__main__':
    unittest.main()