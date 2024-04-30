import unittest

from opensquirrel import circuit_matrix_calculator
from opensquirrel.default_gates import *
from opensquirrel.squirrel_ir import Qubit, SquirrelIR


class CircuitMatrixCalculatorTest(unittest.TestCase):
    def test_hadamard(self):
        register_manager = RegisterManager(qubit_register_size=1)
        squirrel_ir = SquirrelIR()
        squirrel_ir.add_gate(H(Qubit(0)))

        self.assertTrue(
            np.allclose(
                circuit_matrix_calculator.get_circuit_matrix(squirrel_ir),
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
        squirrel_ir = SquirrelIR(qubit_register_size=1)
        squirrel_ir.add_gate(H(Qubit(0)))
        squirrel_ir.add_gate(H(Qubit(0)))

        self.assertTrue(np.allclose(circuit_matrix_calculator.get_circuit_matrix(squirrel_ir), np.eye(2)))

    def test_triple_hadamard(self):
        squirrel_ir = SquirrelIR(qubit_register_size=1)
        squirrel_ir.add_gate(H(Qubit(0)))
        squirrel_ir.add_gate(H(Qubit(0)))
        squirrel_ir.add_gate(H(Qubit(0)))

        self.assertTrue(
            np.allclose(
                circuit_matrix_calculator.get_circuit_matrix(squirrel_ir),
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
        squirrel_ir = SquirrelIR(qubit_register_size=2)
        squirrel_ir.add_gate(H(Qubit(0)))
        squirrel_ir.add_gate(X(Qubit(1)))

        self.assertTrue(
            np.allclose(
                circuit_matrix_calculator.get_circuit_matrix(squirrel_ir),
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
        squirrel_ir = SquirrelIR(qubit_register_size=2)
        squirrel_ir.add_gate(H(Qubit(1)))
        squirrel_ir.add_gate(X(Qubit(0)))

        self.assertTrue(
            np.allclose(
                circuit_matrix_calculator.get_circuit_matrix(squirrel_ir),
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
        squirrel_ir = SquirrelIR(qubit_register_size=2)
        squirrel_ir.add_gate(CNOT(Qubit(1), Qubit(0)))

        self.assertTrue(
            np.allclose(
                circuit_matrix_calculator.get_circuit_matrix(squirrel_ir),
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
        squirrel_ir = SquirrelIR(qubit_register_size=2)
        squirrel_ir.add_gate(CNOT(Qubit(0), Qubit(1)))

        self.assertTrue(
            np.allclose(
                circuit_matrix_calculator.get_circuit_matrix(squirrel_ir),
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
        squirrel_ir = SquirrelIR(qubit_register_size=2)
        squirrel_ir.add_gate(H(Qubit(0)))
        squirrel_ir.add_gate(CNOT(Qubit(0), Qubit(1)))

        self.assertTrue(
            np.allclose(
                circuit_matrix_calculator.get_circuit_matrix(squirrel_ir),
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

    def test_hadamard_cnot_0_2(self):
        squirrel_ir = SquirrelIR(qubit_register_size=3)
        squirrel_ir.add_gate(H(Qubit(0)))
        squirrel_ir.add_gate(CNOT(Qubit(0), Qubit(2)))

        print(circuit_matrix_calculator.get_circuit_matrix(squirrel_ir))
        self.assertTrue(
            np.allclose(
                circuit_matrix_calculator.get_circuit_matrix(squirrel_ir),
                math.sqrt(0.5)
                * np.array(
                    [
                        [1, 1, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 1, -1, 0, 0],
                        [0, 0, 1, 1, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 1, -1],
                        [0, 0, 0, 0, 1, 1, 0, 0],
                        [1, -1, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 1, 1],
                        [0, 0, 1, -1, 0, 0, 0, 0],
                    ]
                ),
            )
        )


if __name__ == "__main__":
    unittest.main()
