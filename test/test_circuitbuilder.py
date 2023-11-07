from src.CircuitBuilder import CircuitBuilder
from test.TestGates import TEST_GATES
import unittest

class CircuitBuilderTest(unittest.TestCase):
    def test_simple(self):
        builder = CircuitBuilder(TEST_GATES, 3)

        builder.h(0)
        builder.cnot(0, 1)

        circuit = builder.to_circuit()

        self.assertEqual(circuit.getNumberOfQubits(), 3)
        self.assertEqual(circuit.getQubitRegisterName(), "q")
        self.assertEqual(len(circuit.squirrelAST.operations), 2)
        self.assertEqual(circuit.squirrelAST.operations[0], ("h", (0,)))
        self.assertEqual(circuit.squirrelAST.operations[1], ("cnot", (0,1)))


    def test_chain(self):
        builder = CircuitBuilder(TEST_GATES, 3)

        circuit = builder.h(0).cnot(0, 1).to_circuit()

        self.assertEqual(len(circuit.squirrelAST.operations), 2)
        self.assertEqual(circuit.squirrelAST.operations[0], ("h", (0,)))
        self.assertEqual(circuit.squirrelAST.operations[1], ("cnot", (0,1)))


    def test_unknown_gate(self):
        builder = CircuitBuilder(TEST_GATES, 3)
        
        with self.assertRaisesRegex(Exception, "Unknown gate or alias of gate: `un`"):
            builder.un(0)


    def test_wrong_number_of_arguments(self):
        builder = CircuitBuilder(TEST_GATES, 3)
        
        with self.assertRaisesRegex(AssertionError, "Wrong number of arguments for gate `h`"):
            builder.h(0, 1)