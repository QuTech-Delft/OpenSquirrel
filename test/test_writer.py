import unittest

from opensquirrel.default_gates import DefaultGates
from opensquirrel.squirrel_ast import SquirrelAST
from opensquirrel.writer import Writer


class WriterTest(unittest.TestCase):
    def test_write(self):
        squirrelAST = SquirrelAST(DefaultGates, 3, "myqubitsregister")

        writer = Writer(DefaultGates)

        written = writer.process(squirrelAST)

        self.assertEqual(
            written,
            """version 3.0

qubit[3] myqubitsregister

""",
        )

        squirrelAST.addGate("h", 0)
        squirrelAST.addGate("cr", 0, 1, 1.234)

        written = writer.process(squirrelAST)

        self.assertEqual(
            written,
            """version 3.0

qubit[3] myqubitsregister

h myqubitsregister[0]
cr myqubitsregister[0], myqubitsregister[1], 1.234
""",
        )

    def test_comment(self):
        squirrelAST = SquirrelAST(DefaultGates, 3, "q")

        writer = Writer(DefaultGates)

        squirrelAST.addGate("h", 0)
        squirrelAST.addComment("My comment")
        squirrelAST.addGate("cr", 0, 1, 1.234)

        self.assertEqual(
            writer.process(squirrelAST),
            """version 3.0

qubit[3] q

h q[0]

/* My comment */

cr q[0], q[1], 1.234
""",
        )

    def test_cap_significant_digits(self):
        squirrelAST = SquirrelAST(DefaultGates, 3, "q")

        writer = Writer(DefaultGates)

        squirrelAST.addGate("cr", 0, 1, 1.6546514861321684321654)

        self.assertEqual(
            writer.process(squirrelAST),
            """version 3.0

qubit[3] q

cr q[0], q[1], 1.6546515
""",
        )


if __name__ == "__main__":
    unittest.main()
