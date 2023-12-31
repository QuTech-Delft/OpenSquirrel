import unittest

import antlr4

from opensquirrel.default_gates import DefaultGates
from opensquirrel.parsing.antlr.generated import CQasm3Lexer, CQasm3Parser
from opensquirrel.parsing.antlr.squirrel_ast_creator import SquirrelASTCreator
from opensquirrel.squirrel_error_handler import SquirrelErrorHandler, SquirrelParseException
from opensquirrel.type_checker import TypeChecker


class ParsingTest(unittest.TestCase):
    def setUp(self):
        self.gates = DefaultGates
        self.astCreator = SquirrelASTCreator(DefaultGates)

    def typeCheck(self, cQasm3String):
        input_stream = antlr4.InputStream(cQasm3String)

        lexer = CQasm3Lexer.CQasm3Lexer(input_stream)

        stream = antlr4.CommonTokenStream(lexer)

        parser = CQasm3Parser.CQasm3Parser(stream)

        parser.removeErrorListeners()
        parser.addErrorListener(SquirrelErrorHandler())

        tree = parser.prog()

        typeChecker = TypeChecker(self.gates)
        typeChecker.visit(tree)

        return tree

    def getAST(self, cQasm3String):
        tree = self.typeCheck(cQasm3String)
        return self.astCreator.visit(tree)

    def test_empty(self):
        with self.assertRaisesRegex(SquirrelParseException, "Parsing error at 1:0: mismatched input '<EOF>' expecting"):
            self.typeCheck("")

    def test_illegal(self):
        with self.assertRaisesRegex(
            SquirrelParseException, "Parsing error at 1:0: mismatched input 'illegal' expecting"
        ):
            self.typeCheck("illegal")

    def test_no_qubits(self):
        with self.assertRaisesRegex(
            SquirrelParseException, "Parsing error at 1:14: mismatched input 'h' expecting 'qubit"
        ):
            self.typeCheck("version 3.0;  h q[0]")

    def test_wrong_version(self):
        with self.assertRaisesRegex(
            SquirrelParseException, "Parsing error at 1:8: mismatched input '3.1' expecting '3.0'"
        ):
            self.typeCheck("version 3.1; qubit[1] q; h q[0]")

    def test_unknown_gate(self):
        with self.assertRaisesRegex(Exception, "Unknown gate `unknowngate`"):
            self.typeCheck("version 3.0; qubit[1] q; unknowngate q[0]")

    def test_wrong_argument_type(self):
        with self.assertRaisesRegex(
            Exception, "Argument #1 passed to gate `rx` is of type ArgType.INT but should be ArgType.FLOAT"
        ):
            self.typeCheck("version 3.0; qubit[1] q; rx q[0], 42")

    def test_wrong_argument_type_2(self):
        with self.assertRaisesRegex(
            Exception, "Argument #0 passed to gate `rx` is of type ArgType.FLOAT but should be ArgType.QUBIT"
        ):
            self.typeCheck("version 3.0; qubit[1] q; rx 42., q[0]")

    # FIXME: add comments to AST when parsing?

    def test_simple(self):
        ast = self.getAST(
            """
            version 3.0

            qubit[1] qu

            h qu[0]
        """
        )

        self.assertEqual(ast.nQubits, 1)
        self.assertEqual(ast.qubitRegisterName, "qu")
        self.assertEqual(len(ast.operations), 1)
        self.assertEqual(ast.operations[0], ("h", (0,)))

    def test_r_xyz(self):
        ast = self.getAST(
            """
version 3.0
  qubit[2] squirrel

  h squirrel[0];
  rx squirrel[1], 1.23;;;;;
  ry squirrel[0], -42.;;;;;
        """
        )

        self.assertEqual(ast.nQubits, 2)
        self.assertEqual(ast.qubitRegisterName, "squirrel")
        self.assertEqual(len(ast.operations), 3)
        self.assertEqual(ast.operations[0], ("h", (0,)))
        self.assertEqual(ast.operations[1], ("rx", (1, 1.23)))
        self.assertEqual(ast.operations[2], ("ry", (0, -42)))

    def test_multiple_qubits(self):
        ast = self.getAST(
            """
version 3.0
  qubit[10] large

  h large[0,3,6];
  x90 large[4:5];
        """
        )

        self.assertEqual(ast.nQubits, 10)
        self.assertEqual(ast.qubitRegisterName, "large")
        self.assertEqual(len(ast.operations), 5)
        self.assertEqual(ast.operations[0], ("h", (0,)))
        self.assertEqual(ast.operations[1], ("h", (3,)))
        self.assertEqual(ast.operations[2], ("h", (6,)))
        self.assertEqual(ast.operations[3], ("x90", (4,)))
        self.assertEqual(ast.operations[4], ("x90", (5,)))

    def test_aliases(self):
        ast = self.getAST(
            """
version 3.0
  qubit[2] q;

  H q[1]
        """
        )

        self.assertEqual(ast.operations[0], ("H", (1,)))


if __name__ == "__main__":
    unittest.main()
