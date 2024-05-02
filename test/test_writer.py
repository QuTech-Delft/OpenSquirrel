import unittest

from opensquirrel.circuit import Circuit
from opensquirrel.default_gates import *
from opensquirrel.exporter import writer
from opensquirrel.register_manager import RegisterManager
from opensquirrel.squirrel_ir import Comment, Float, Qubit, SquirrelIR


class WriterTest(unittest.TestCase):
    def test_write(self):
        register_manager = RegisterManager(qubit_register_size=3)
        squirrel_ir = SquirrelIR()
        circuit = Circuit(register_manager, squirrel_ir)

        self.assertEqual(
            writer.circuit_to_string(circuit),
            """version 3.0

qubit[3] q

""",
        )

        squirrel_ir.add_gate(H(Qubit(0)))
        squirrel_ir.add_gate(CR(Qubit(0), Qubit(1), Float(1.234)))
        circuit = Circuit(register_manager, squirrel_ir)

        self.assertEqual(
            writer.circuit_to_string(circuit),
            """version 3.0

qubit[3] q

H q[0]
CR q[0], q[1], 1.234
""",
        )

    def test_anonymous_gate(self):
        register_manager = RegisterManager(qubit_register_size=2)
        squirrel_ir = SquirrelIR()
        squirrel_ir.add_gate(CR(Qubit(0), Qubit(1), Float(1.234)))
        squirrel_ir.add_gate(BlochSphereRotation(Qubit(0), axis=(1, 1, 1), angle=1.23))
        squirrel_ir.add_gate(CR(Qubit(0), Qubit(1), Float(1.234)))
        circuit = Circuit(register_manager, squirrel_ir)

        self.assertEqual(
            writer.circuit_to_string(circuit),
            """version 3.0

qubit[2] q

CR q[0], q[1], 1.234
<anonymous-gate>
CR q[0], q[1], 1.234
""",
        )

    def test_comment(self):
        register_manager = RegisterManager(qubit_register_size=3)
        squirrel_ir = SquirrelIR()
        squirrel_ir.add_gate(H(Qubit(0)))
        squirrel_ir.add_comment(Comment("My comment"))
        squirrel_ir.add_gate(CR(Qubit(0), Qubit(1), Float(1.234)))
        circuit = Circuit(register_manager, squirrel_ir)

        self.assertEqual(
            writer.circuit_to_string(circuit),
            """version 3.0

qubit[3] q

H q[0]

/* My comment */

CR q[0], q[1], 1.234
""",
        )

    def test_cap_significant_digits(self):
        register_manager = RegisterManager(qubit_register_size=3)
        squirrel_ir = SquirrelIR()
        squirrel_ir.add_gate(CR(Qubit(0), Qubit(1), Float(1.6546514861321684321654)))
        circuit = Circuit(register_manager, squirrel_ir)

        self.assertEqual(
            writer.circuit_to_string(circuit),
            """version 3.0

qubit[3] q

CR q[0], q[1], 1.6546515
""",
        )


if __name__ == "__main__":
    unittest.main()
