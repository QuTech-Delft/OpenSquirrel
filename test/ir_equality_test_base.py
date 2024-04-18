import unittest

from opensquirrel import circuit_matrix_calculator
from opensquirrel.common import are_matrices_equivalent_up_to_global_phase


class IREqualityTestBase(unittest.TestCase):
    def check_equivalence_up_to_global_phase(self, matrix_a, matrix_b):
        self.assertTrue(are_matrices_equivalent_up_to_global_phase(matrix_a, matrix_b))

    def modify_ir_and_check(self, ir, action, expected_ir=None):
        """
        Checks whether the IR action preserves:
        - the number of qubits,
        - the qubit register name(s),
        - the circuit matrix up to a global phase factor.
        """

        # Store matrix before decompositions.
        expected_matrix = circuit_matrix_calculator.get_circuit_matrix(ir)

        expected_number_of_qubits = ir.number_of_qubits
        expected_qubit_register_name = ir.qubit_register_name

        action(ir)

        self.assertEqual(ir.number_of_qubits, expected_number_of_qubits)
        self.assertEqual(ir.qubit_register_name, expected_qubit_register_name)

        # Get matrix after decompositions.
        actual_matrix = circuit_matrix_calculator.get_circuit_matrix(ir)

        self.check_equivalence_up_to_global_phase(actual_matrix, expected_matrix)

        if expected_ir is not None:
            self.assertEqual(ir, expected_ir)
