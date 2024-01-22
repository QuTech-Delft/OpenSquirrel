import unittest

from opensquirrel.default_gates import *
from opensquirrel.parsing.libqasm.libqasm_ir_creator import LibqasmIRCreator


class LibqasmTest(unittest.TestCase):
    def setUp(self):
        self.libqasm_ir_creator = LibqasmIRCreator(gate_set=default_gate_set, gate_aliases=default_gate_aliases)

    def test_simple(self):
        ir = self.libqasm_ir_creator.squirrel_ir_from_string(
            """
version 3.0

qubit[2] my_qubits

h my_qubits[0]
ry my_qubits[1], 1.234
cnot my_qubits[0], my_qubits[1]
cr my_qubits[1], my_qubits[0], 5.123
crk my_qubits[0], my_qubits[1], 23
        """
        )

        self.assertEqual(ir.number_of_qubits, 2)
        self.assertEqual(ir.qubit_register_name, "my_qubits")
        self.assertEqual(
            ir.statements,
            [
                h(Qubit(0)),
                ry(Qubit(1), Float(1.234)),
                cnot(Qubit(0), Qubit(1)),
                cr(Qubit(1), Qubit(0), Float(5.123)),
                crk(Qubit(0), Qubit(1), Int(23)),
            ],
        )

    def test_sgmq(self):
        ir = self.libqasm_ir_creator.squirrel_ir_from_string(
            """
version 3.0

qubit[20] q

h q[5:9]
x q[13,17]
crk q[0, 3], q[1, 4], 23
        """
        )

        self.assertEqual(ir.number_of_qubits, 20)
        self.assertEqual(ir.qubit_register_name, "q")
        self.assertEqual(
            ir.statements,
            [
                h(Qubit(5)),
                h(Qubit(6)),
                h(Qubit(7)),
                h(Qubit(8)),
                h(Qubit(9)),
                x(Qubit(13)),
                x(Qubit(17)),
                crk(Qubit(0), Qubit(1), Int(23)),
                crk(Qubit(3), Qubit(4), Int(23)),
            ],
        )

    def test_error(self):
        with self.assertRaisesRegex(Exception, "Error at <unknown>:1:30..31: failed to resolve mapping 'q'"):
            self.libqasm_ir_creator.squirrel_ir_from_string("""version 3.0; qubit[20] qu; h q[5]""")

    def test_multiple_qubit_registers_not_supported(self):
        with self.assertRaisesRegex(
            Exception, "OpenSquirrel currently supports only a single qubit array variable in cQasm 3.0"
        ):
            self.libqasm_ir_creator.squirrel_ir_from_string("""version 3.0; qubit[20] qu; qubit[20] quux; h qu[5]""")

    def test_bit_register_not_supported(self):
        with self.assertRaisesRegex(
            Exception, "OpenSquirrel currently supports only a single qubit array variable in cQasm 3.0"
        ):
            self.libqasm_ir_creator.squirrel_ir_from_string("""version 3.0; qubit[1] q; bit[1] b; h q[0]""")

    def test_wrong_gate_argument_number_or_types(self):
        with self.assertRaisesRegex(
            Exception,
            r"Parsing error: Error at <unknown>:1:26\.\.27: failed to resolve overload for h with argument pack \(qubit, int\)",
        ):
            self.libqasm_ir_creator.squirrel_ir_from_string("""version 3.0; qubit[1] q; h q[0], 1""")

        with self.assertRaisesRegex(
            Exception,
            r"Parsing error: Error at <unknown>:1:26\.\.30: failed to resolve overload for cnot with argument pack \(qubit, int\)",
        ):
            self.libqasm_ir_creator.squirrel_ir_from_string("""version 3.0; qubit[1] q; cnot q[0], 1""")
