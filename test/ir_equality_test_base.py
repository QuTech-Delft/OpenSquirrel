import unittest

from opensquirrel import circuit_matrix_calculator
from opensquirrel.circuit import Circuit
from opensquirrel.common import are_matrices_equivalent_up_to_global_phase


class IREqualityTestBase(unittest.TestCase):
    def check_equivalence_up_to_global_phase(self, matrix_a, matrix_b):
        self.assertTrue(are_matrices_equivalent_up_to_global_phase(matrix_a, matrix_b))

    def modify_circuit_and_check(self, circuit, action, expected_circuit=None):
        """
        Checks whether the action preserves:
        - the number of qubits,
        - the qubit register name(s),
        - the circuit matrix up to a global phase factor.
        """

        # Store matrix before decompositions.
        expected_matrix = circuit_matrix_calculator.get_circuit_matrix(circuit)

        action(circuit)

        # Get matrix after decompositions.
        actual_matrix = circuit_matrix_calculator.get_circuit_matrix(circuit)

        self.check_equivalence_up_to_global_phase(actual_matrix, expected_matrix)

        if expected_circuit is not None:
            self.assertEqual(circuit, expected_circuit)
