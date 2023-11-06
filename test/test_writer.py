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


if __name__ == '__main__':
    unittest.main()

