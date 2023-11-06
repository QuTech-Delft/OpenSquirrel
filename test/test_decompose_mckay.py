from test.TestGates import TEST_GATES
from test.TestHelpers import areMatricesEqualUpToGlobalPhase
from src.SquirrelAST import SquirrelAST
from src.TestInterpreter import TestInterpreter
from src.McKayDecomposer import McKayDecomposer
import unittest

class DecomposeMcKayTests(unittest.TestCase):
    def checkMcKayDecomposition(self, squirrelAST, expectedAST = None):
        """
            Check whether the mcKay decomposition transformation applied to the input AST preserves the
            circuit matrix up to an irrelevant global phase factor.
        """

        interpreter = TestInterpreter(squirrelAST.gates)
        # Store matrix before decompositions.
        expectedMatrix = interpreter.process(squirrelAST)

        decomposer = McKayDecomposer(squirrelAST.gates)
        output = decomposer.process(squirrelAST)

        self.assertEqual(output.nQubits, squirrelAST.nQubits)
        self.assertEqual(output.qubitRegisterName, squirrelAST.qubitRegisterName)

        if expectedAST is not None:
            self.assertEqual(output, expectedAST)

        # Get matrix after decompositions.
        actualMatrix = interpreter.process(output)

        self.assertTrue(areMatricesEqualUpToGlobalPhase(actualMatrix, expectedMatrix))

    def test_one(self):
        ast = SquirrelAST(TEST_GATES, 2, "squirrel")

        ast.addGate("ry", 0, 23847628349.123)
        ast.addGate("rx", 0, 29384672.234)
        ast.addGate("rz", 0, 9877.87634)

        self.checkMcKayDecomposition(ast)

    def test_two(self):
        ast = SquirrelAST(TEST_GATES, 2, "squirrel")

        ast.addGate("ry", 0, 23847628349.123)
        ast.addGate("cnot", 0, 1)
        ast.addGate("rx", 0, 29384672.234)
        ast.addGate("rz", 0, 9877.87634)
        ast.addGate("cnot", 0, 1)
        ast.addGate("rx", 0, 29384672.234)
        ast.addGate("rz", 0, 9877.87634)

        self.checkMcKayDecomposition(ast)


    def test_smallrandom(self):
        ast = SquirrelAST(TEST_GATES, 4, "q")

        ast.addGate("H", 2)
        ast.addGate("cr", 2, 3, 2.123)
        ast.addGate("H", 1)
        ast.addGate("H", 0)
        ast.addGate("H", 2)
        ast.addGate("H", 1)
        ast.addGate("H", 0)
        ast.addGate("cr", 2, 3, 2.123)


        expectedAst = SquirrelAST(TEST_GATES, 4, "q")

        expectedAst.addGate("x90", 2)
        expectedAst.addGate("rz", 2, 1.5707963267948966)
        expectedAst.addGate("x90", 2)
        expectedAst.addGate("cr", 2, 3, 2.123)
        expectedAst.addGate("x90", 2)
        expectedAst.addGate("rz", 2, 1.5707963267948966)
        expectedAst.addGate("x90", 2)
        expectedAst.addGate("cr", 2, 3, 2.123)

        self.checkMcKayDecomposition(ast, expectedAst)

if __name__ == '__main__':
    unittest.main()