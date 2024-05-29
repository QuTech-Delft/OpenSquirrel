import unittest

from opensquirrel.circuit import Circuit
from opensquirrel.default_gates import *
from opensquirrel.exporter import writer
from opensquirrel.ir import IR, Comment, Float, Qubit
from opensquirrel.register_manager import RegisterManager


class WriterTest(unittest.TestCase):
    def test_write(self):
        register_manager = RegisterManager(qubit_register_size=3)
        ir = IR()
        circuit = Circuit(register_manager, ir)

        self.assertEqual(
            writer.circuit_to_string(circuit),
            """version 3.0

qubit[3] q

""",
        )

        ir.add_gate(H(Qubit(0)))
        ir.add_gate(CR(Qubit(0), Qubit(1), Float(1.234)))
        circuit = Circuit(register_manager, ir)

        self.assertEqual(
            writer.circuit_to_string(circuit),
            """version 3.0

qubit[3] q

H q[0]
CR(1.234) q[0], q[1]
""",
        )

    def test_anonymous_gate(self):
        register_manager = RegisterManager(qubit_register_size=2)
        ir = IR()
        ir.add_gate(CR(Qubit(0), Qubit(1), Float(1.234)))
        ir.add_gate(BlochSphereRotation(Qubit(0), axis=(1, 1, 1), angle=1.23))
        ir.add_gate(CR(Qubit(0), Qubit(1), Float(1.234)))
        circuit = Circuit(register_manager, ir)

        self.assertEqual(
            writer.circuit_to_string(circuit),
            """version 3.0

qubit[2] q

CR(1.234) q[0], q[1]
<anonymous-gate>
CR(1.234) q[0], q[1]
""",
        )

    def test_comment(self):
        register_manager = RegisterManager(qubit_register_size=3)
        ir = IR()
        ir.add_gate(H(Qubit(0)))
        ir.add_comment(Comment("My comment"))
        ir.add_gate(CR(Qubit(0), Qubit(1), Float(1.234)))
        circuit = Circuit(register_manager, ir)

        self.assertEqual(
            writer.circuit_to_string(circuit),
            """version 3.0

qubit[3] q

H q[0]

/* My comment */

CR(1.234) q[0], q[1]
""",
        )

    def test_cap_significant_digits(self):
        register_manager = RegisterManager(qubit_register_size=3)
        ir = IR()
        ir.add_gate(CR(Qubit(0), Qubit(1), Float(1.6546514861321684321654)))
        circuit = Circuit(register_manager, ir)

        self.assertEqual(
            writer.circuit_to_string(circuit),
            """version 3.0

qubit[3] q

CR(1.6546515) q[0], q[1]
""",
        )


if __name__ == "__main__":
    unittest.main()
