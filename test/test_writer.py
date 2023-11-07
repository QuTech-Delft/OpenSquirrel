import unittest
from test.TestGates import TEST_GATES
from src.SquirrelAST import SquirrelAST
from src.Writer import Writer

class WriterTest(unittest.TestCase):
    def test_write(self):
        squirrelAST = SquirrelAST(TEST_GATES, 3, "myqubitsregister")

        writer = Writer(TEST_GATES)

        written = writer.process(squirrelAST)
        
        self.assertEqual(written, """version 3.0

qubit[3] myqubitsregister

""")

        squirrelAST.addGate("h", 0)
        squirrelAST.addGate("cr", 0, 1, 1.234)

        written = writer.process(squirrelAST)

        self.assertEqual(written, """version 3.0

qubit[3] myqubitsregister

h myqubitsregister[0]
cr myqubitsregister[0], myqubitsregister[1], 1.234
""")

    def test_comment(self):
        squirrelAST = SquirrelAST(TEST_GATES, 3, "q")

        writer = Writer(TEST_GATES)

        squirrelAST.addGate("h", 0)
        squirrelAST.addComment("My comment")
        squirrelAST.addGate("cr", 0, 1, 1.234)

        self.assertEqual(writer.process(squirrelAST), """version 3.0

qubit[3] q

h q[0]

/* My comment */

cr q[0], q[1], 1.234
""")


if __name__ == '__main__':
    unittest.main()

