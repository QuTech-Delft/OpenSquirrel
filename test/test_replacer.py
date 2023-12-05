import unittest

from opensquirrel import replacer
from opensquirrel.default_gates import *
from opensquirrel.squirrel_ir import Qubit, SquirrelIR


def hadamard_decomposition(q: Qubit):
    return [
        y90(q),
        x(q),
    ]


class ReplacerTest(unittest.TestCase):
    def test_replace(self):
        squirrel_ir = SquirrelIR(number_of_qubits=3, qubit_register_name="test")

        squirrel_ir.add_gate(h(Qubit(0)))
        squirrel_ir.add_comment(Comment("Test comment."))

        replacer.replace(squirrel_ir, "h", hadamard_decomposition)

        expected_ir = SquirrelIR(number_of_qubits=3, qubit_register_name="test")

        expected_ir.add_gate(y90(Qubit(0)))
        expected_ir.add_gate(x(Qubit(0)))
        expected_ir.add_comment(Comment("Test comment."))

        self.assertEqual(expected_ir, squirrel_ir)


if __name__ == "__main__":
    unittest.main()
