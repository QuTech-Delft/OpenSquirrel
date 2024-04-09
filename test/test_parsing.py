import unittest

import antlr4

from opensquirrel.default_gates import *
from opensquirrel.parsing.antlr.generated import CQasm3Lexer, CQasm3Parser
from opensquirrel.parsing.antlr.squirrel_error_handler import SquirrelErrorHandler, SquirrelParseException
from opensquirrel.parsing.antlr.squirrel_ir_creator import SquirrelIRCreator
from opensquirrel.parsing.antlr.type_checker import TypeChecker


class ParsingTest(unittest.TestCase):
    def setUp(self):
        self.ir_creator = SquirrelIRCreator()

    @staticmethod
    def type_check(cqasm_string):
        input_stream = antlr4.InputStream(cqasm_string)

        lexer = CQasm3Lexer.CQasm3Lexer(input_stream)

        stream = antlr4.CommonTokenStream(lexer)

        parser = CQasm3Parser.CQasm3Parser(stream)

        parser.removeErrorListeners()
        parser.addErrorListener(SquirrelErrorHandler())

        tree = parser.prog()

        type_checker = TypeChecker()
        type_checker.visit(tree)

        return tree

    def get_ir(self, cqasm_string):
        tree = self.type_check(cqasm_string)
        return self.ir_creator.visit(tree)

    def test_empty(self):
        with self.assertRaisesRegex(SquirrelParseException, "Parsing error at 1:0: mismatched input '<EOF>' expecting"):
            self.type_check("")

    def test_illegal(self):
        with self.assertRaisesRegex(
            SquirrelParseException, "Parsing error at 1:0: mismatched input 'illegal' expecting"
        ):
            self.type_check("illegal")

    def test_no_qubits(self):
        with self.assertRaisesRegex(
            SquirrelParseException, "Parsing error at 1:14: mismatched input 'h' expecting 'qubit"
        ):
            self.type_check("version 3.0;  h q[0]")

    def test_wrong_version(self):
        with self.assertRaisesRegex(
            SquirrelParseException, "Parsing error at 1:8: mismatched input '3.1' expecting '3.0'"
        ):
            self.type_check("version 3.1; qubit[1] q; H q[0]")

    def test_unknown_gate(self):
        with self.assertRaisesRegex(Exception, "Unknown gate `unknowngate`"):
            self.type_check("version 3.0; qubit[1] q; unknowngate q[0]")

    def test_wrong_argument_type(self):
        with self.assertRaisesRegex(
            Exception,
            "Argument #1 passed to gate `Rx` is of type <class 'opensquirrel.squirrel_ir.Int'> but should be <class 'opensquirrel.squirrel_ir.Float'>",
        ):
            self.type_check("version 3.0; qubit[1] q; Rx q[0], 42")

    def test_wrong_argument_type_2(self):
        with self.assertRaisesRegex(
            Exception,
            "Argument #0 passed to gate `Rx` is of type <class 'opensquirrel.squirrel_ir.Float'> but should be <class 'opensquirrel.squirrel_ir.Qubit'>",
        ):
            self.type_check("version 3.0; qubit[1] q; Rx 42., q[0]")

    # FIXME: add comments to IR when parsing?

    def test_simple(self):
        ir = self.get_ir(
            """
            version 3.0

            qubit[1] qu

            H qu[0]
        """
        )

        self.assertEqual(ir.number_of_qubits, 1)
        self.assertEqual(ir.qubit_register_name, "qu")
        self.assertEqual(len(ir.statements), 1)
        self.assertEqual(ir.statements[0], H(Qubit(0)))

    def test_r_xyz(self):
        ir = self.get_ir(
            """
version 3.0
  qubit[2] squirrel

  H squirrel[0];
  Rx squirrel[1], 1.23;;;;;
  Ry squirrel[0], -42.;;;;;
        """
        )

        self.assertEqual(ir.number_of_qubits, 2)
        self.assertEqual(ir.qubit_register_name, "squirrel")
        self.assertEqual(len(ir.statements), 3)
        self.assertEqual(ir.statements[0], H(Qubit(0)))
        self.assertEqual(ir.statements[1], Rx(Qubit(1), Float(1.23)))
        self.assertEqual(ir.statements[2], Ry(Qubit(0), Float(-42)))

    def test_multiple_qubits(self):
        ir = self.get_ir(
            """
version 3.0
  qubit[10] large

  H large[0,3,6];
  X90 large[4:5];
        """
        )

        self.assertEqual(ir.number_of_qubits, 10)
        self.assertEqual(ir.qubit_register_name, "large")
        self.assertEqual(len(ir.statements), 5)
        self.assertEqual(ir.statements[0], H(Qubit(0)))
        self.assertEqual(ir.statements[1], H(Qubit(3)))
        self.assertEqual(ir.statements[2], H(Qubit(6)))
        self.assertEqual(ir.statements[3], X90(Qubit(4)))
        self.assertEqual(ir.statements[4], X90(Qubit(5)))

    def test_aliases(self):
        ir = self.get_ir(
            """
version 3.0
  qubit[2] q;

  Hadamard q[1]
        """
        )

        self.assertEqual(ir.statements[0], H(Qubit(1)))


if __name__ == "__main__":
    unittest.main()
