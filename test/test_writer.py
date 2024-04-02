import unittest

from opensquirrel import writer
from opensquirrel.default_gates import *
from opensquirrel.squirrel_ir import Comment, Float, Qubit, SquirrelIR


class WriterTest(unittest.TestCase):
    def test_write(self):
        squirrel_ir = SquirrelIR(number_of_qubits=3, qubit_register_name="myqubitsregister")

        written = writer.squirrel_ir_to_string(squirrel_ir)

        self.assertEqual(
            written,
            """version 3.0

qubit[3] myqubitsregister

""",
        )

        squirrel_ir.add_gate(H(Qubit(0)))
        squirrel_ir.add_gate(CR(Qubit(0), Qubit(1), Float(1.234)))

        written = writer.squirrel_ir_to_string(squirrel_ir)

        self.assertEqual(
            written,
            """version 3.0

qubit[3] myqubitsregister

H myqubitsregister[0]
CR myqubitsregister[0], myqubitsregister[1], 1.234
""",
        )

    def test_anonymous_gate(self):
        squirrel_ir = SquirrelIR(number_of_qubits=1, qubit_register_name="q")

        squirrel_ir.add_gate(CR(Qubit(0), Qubit(1), Float(1.234)))
        squirrel_ir.add_gate(BlochSphereRotation(Qubit(0), axis=(1, 1, 1), angle=1.23))
        squirrel_ir.add_gate(CR(Qubit(0), Qubit(1), Float(1.234)))

        self.assertEqual(
            writer.squirrel_ir_to_string(squirrel_ir),
            """version 3.0

qubit[1] q

CR q[0], q[1], 1.234
<anonymous-gate>
CR q[0], q[1], 1.234
""",
        )

    def test_comment(self):
        squirrel_ir = SquirrelIR(number_of_qubits=3, qubit_register_name="q")

        squirrel_ir.add_gate(H(Qubit(0)))
        squirrel_ir.add_comment(Comment("My comment"))
        squirrel_ir.add_gate(CR(Qubit(0), Qubit(1), Float(1.234)))

        self.assertEqual(
            writer.squirrel_ir_to_string(squirrel_ir),
            """version 3.0

qubit[3] q

H q[0]

/* My comment */

CR q[0], q[1], 1.234
""",
        )

    def test_cap_significant_digits(self):
        squirrel_ir = SquirrelIR(number_of_qubits=3, qubit_register_name="q")

        squirrel_ir.add_gate(CR(Qubit(0), Qubit(1), Float(1.6546514861321684321654)))

        self.assertEqual(
            writer.squirrel_ir_to_string(squirrel_ir),
            """version 3.0

qubit[3] q

CR q[0], q[1], 1.6546515
""",
        )


if __name__ == "__main__":
    unittest.main()
