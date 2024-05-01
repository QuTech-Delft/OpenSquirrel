import unittest

from opensquirrel import circuit_matrix_calculator
from opensquirrel.circuit import Circuit
from opensquirrel.default_gates import *
from opensquirrel.register_manager import RegisterManager
from opensquirrel.squirrel_ir import Qubit, SquirrelIR


class CircuitMatrixCalculatorTest(unittest.TestCase):
    def test_hadamard(self):
        register_manager = RegisterManager(qubit_register_size=1)
        squirrel_ir = SquirrelIR()
        squirrel_ir.add_gate(H(Qubit(0)))
        circuit = Circuit(register_manager, squirrel_ir)

        self.assertTrue(
            np.allclose(
                circuit_matrix_calculator.get_circuit_matrix(circuit),
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
        register_manager = RegisterManager(qubit_register_size=1)
        squirrel_ir = SquirrelIR()
        squirrel_ir.add_gate(H(Qubit(0)))
        squirrel_ir.add_gate(H(Qubit(0)))
        circuit = Circuit(register_manager, squirrel_ir)

        self.assertTrue(np.allclose(circuit_matrix_calculator.get_circuit_matrix(circuit), np.eye(2)))

    def test_triple_hadamard(self):
        register_manager = RegisterManager(qubit_register_size=1)
        squirrel_ir = SquirrelIR()
        squirrel_ir.add_gate(H(Qubit(0)))
        squirrel_ir.add_gate(H(Qubit(0)))
        squirrel_ir.add_gate(H(Qubit(0)))
        circuit = Circuit(register_manager, squirrel_ir)

        self.assertTrue(
            np.allclose(
                circuit_matrix_calculator.get_circuit_matrix(circuit),
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
        register_manager = RegisterManager(qubit_register_size=2)
        squirrel_ir = SquirrelIR()
        squirrel_ir.add_gate(H(Qubit(0)))
        squirrel_ir.add_gate(X(Qubit(1)))
        circuit = Circuit(register_manager, squirrel_ir)

        self.assertTrue(
            np.allclose(
                circuit_matrix_calculator.get_circuit_matrix(circuit),
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
        register_manager = RegisterManager(qubit_register_size=2)
        squirrel_ir = SquirrelIR()
        squirrel_ir.add_gate(H(Qubit(1)))
        squirrel_ir.add_gate(X(Qubit(0)))
        circuit = Circuit(register_manager, squirrel_ir)

        self.assertTrue(
            np.allclose(
                circuit_matrix_calculator.get_circuit_matrix(circuit),
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
        register_manager = RegisterManager(qubit_register_size=2)
        squirrel_ir = SquirrelIR()
        squirrel_ir.add_gate(CNOT(Qubit(1), Qubit(0)))
        circuit = Circuit(register_manager, squirrel_ir)

        self.assertTrue(
            np.allclose(
                circuit_matrix_calculator.get_circuit_matrix(circuit),
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
        register_manager = RegisterManager(qubit_register_size=2)
        squirrel_ir = SquirrelIR()
        squirrel_ir.add_gate(CNOT(Qubit(0), Qubit(1)))
        circuit = Circuit(register_manager, squirrel_ir)

        self.assertTrue(
            np.allclose(
                circuit_matrix_calculator.get_circuit_matrix(circuit),
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
        register_manager = RegisterManager(qubit_register_size=2)
        squirrel_ir = SquirrelIR()
        squirrel_ir.add_gate(H(Qubit(0)))
        squirrel_ir.add_gate(CNOT(Qubit(0), Qubit(1)))
        circuit = Circuit(register_manager, squirrel_ir)

        self.assertTrue(
            np.allclose(
                circuit_matrix_calculator.get_circuit_matrix(circuit),
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
        register_manager = RegisterManager(qubit_register_size=3)
        squirrel_ir = SquirrelIR()
        squirrel_ir.add_gate(H(Qubit(0)))
        squirrel_ir.add_gate(CNOT(Qubit(0), Qubit(2)))
        circuit = Circuit(register_manager, squirrel_ir)

        print(circuit_matrix_calculator.get_circuit_matrix(circuit))
        self.assertTrue(
            np.allclose(
                circuit_matrix_calculator.get_circuit_matrix(circuit),
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
