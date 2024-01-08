import unittest

from opensquirrel.circuit_builder import CircuitBuilder
from opensquirrel.default_gates import *
from opensquirrel.squirrel_ir import Qubit


class CircuitBuilderTest(unittest.TestCase):
    def test_simple(self):
        print(default_gate_aliases)
        builder = CircuitBuilder(3)

        builder.h(Qubit(0))
        builder.cnot(Qubit(0), Qubit(1))

        circuit = builder.to_circuit()

        self.assertEqual(circuit.number_of_qubits, 3)
        self.assertEqual(circuit.qubit_register_name, "q")
        self.assertEqual(
            circuit.squirrel_ir.statements,
            [
                h(Qubit(0)),
                cnot(Qubit(0), Qubit(1)),
            ],
        )

    def test_chain(self):
        builder = CircuitBuilder(3)

        circuit = builder.h(Qubit(0)).cnot(Qubit(0), Qubit(1)).to_circuit()

        self.assertEqual(
            circuit.squirrel_ir.statements,
            [
                h(Qubit(0)),
                cnot(Qubit(0), Qubit(1)),
            ],
        )

    def test_unknown_gate(self):
        builder = CircuitBuilder(3)

        with self.assertRaisesRegex(Exception, "Unknown gate `un`"):
            builder.un(0)

    def test_wrong_number_of_arguments(self):
        builder = CircuitBuilder(3)

        with self.assertRaisesRegex(TypeError, r"h\(\) takes 1 positional argument but 2 were given"):
            builder.h(Qubit(0), Qubit(1))

    def test_wrong_argument_type(self):
        builder = CircuitBuilder(3)

        with self.assertRaisesRegex(
            TypeError,
            "Wrong argument type for gate `h`, got <class 'int'> but expected "
            "<class 'opensquirrel.squirrel_ir.Qubit'>",
        ):
            builder.h(0)


if __name__ == "__main__":
    unittest.main()
