import unittest

from opensquirrel import circuit_matrix_calculator, mckay_decomposer
from opensquirrel.default_gates import *
from opensquirrel.squirrel_ir import Float, Qubit, SquirrelIR


class DecomposeMcKayTests(unittest.TestCase):
    def check_equivalence_up_to_global_phase(self, matrix_a, matrix_b):
        first_non_zero = next(
            (i, j) for i in range(matrix_a.shape[0]) for j in range(matrix_a.shape[1]) if abs(matrix_a[i, j]) > ATOL
        )

        if abs(matrix_b[first_non_zero]) < ATOL:
            return False

        phase_difference = matrix_a[first_non_zero] / matrix_b[first_non_zero]

        self.assertTrue(np.allclose(matrix_a, phase_difference * matrix_b))

    def check_mckay_decomposition(self, squirrel_ir, expected_ir=None):
        """
        Check whether the mcKay decomposition transformation applied to the input IR preserves the
        circuit matrix up to a global phase factor.
        """

        # Store matrix before decompositions.
        expected_matrix = circuit_matrix_calculator.get_circuit_matrix(squirrel_ir)

        output = mckay_decomposer.decompose_mckay(squirrel_ir)

        self.assertEqual(output.number_of_qubits, squirrel_ir.number_of_qubits)
        self.assertEqual(output.qubit_register_name, squirrel_ir.qubit_register_name)

        if expected_ir is not None:
            self.assertEqual(output, expected_ir)

        # Get matrix after decompositions.
        actual_matrix = circuit_matrix_calculator.get_circuit_matrix(output)

        self.check_equivalence_up_to_global_phase(actual_matrix, expected_matrix)

    def test_one(self):
        ir = SquirrelIR(number_of_qubits=2, qubit_register_name="squirrel")

        ir.add_gate(ry(Qubit(0), Float(23847628349.123)))
        ir.add_gate(rx(Qubit(0), Float(29384672.234)))
        ir.add_gate(rz(Qubit(0), Float(9877.87634)))

        self.check_mckay_decomposition(ir)

    def test_two(self):
        ir = SquirrelIR(number_of_qubits=2, qubit_register_name="squirrel")

        ir.add_gate(ry(Qubit(0), Float(23847628349.123)))
        ir.add_gate(cnot(Qubit(0), Qubit(1)))
        ir.add_gate(rx(Qubit(0), Float(29384672.234)))
        ir.add_gate(rz(Qubit(0), Float(9877.87634)))
        ir.add_gate(cnot(Qubit(0), Qubit(1)))
        ir.add_gate(rx(Qubit(0), Float(29384672.234)))
        ir.add_gate(rz(Qubit(0), Float(9877.87634)))

        self.check_mckay_decomposition(ir)

    def test_small_random(self):
        ir = SquirrelIR(number_of_qubits=4, qubit_register_name="q")

        ir.add_gate(h(Qubit(2)))
        ir.add_gate(cr(Qubit(2), Qubit(3), Float(2.123)))
        ir.add_gate(h(Qubit(1)))
        ir.add_gate(h(Qubit(0)))
        ir.add_gate(h(Qubit(2)))
        ir.add_gate(h(Qubit(1)))
        ir.add_gate(h(Qubit(0)))
        ir.add_gate(cr(Qubit(2), Qubit(3), Float(2.123)))

        expected_ir = SquirrelIR(number_of_qubits=4, qubit_register_name="q")

        expected_ir.add_gate(x90(Qubit(2)))
        expected_ir.add_gate(rz(Qubit(2), Float(1.5707963267948966)))
        expected_ir.add_gate(x90(Qubit(2)))
        expected_ir.add_gate(cr(Qubit(2), Qubit(3), Float(2.123)))
        expected_ir.add_gate(x90(Qubit(2)))
        expected_ir.add_gate(rz(Qubit(2), Float(1.5707963267948966)))
        expected_ir.add_gate(x90(Qubit(2)))
        expected_ir.add_gate(cr(Qubit(2), Qubit(3), Float(2.123)))

        self.check_mckay_decomposition(ir, expected_ir)


if __name__ == "__main__":
    unittest.main()
