from parsing.GeneratedParsingCode import CQasm3Parser
from parsing.GeneratedParsingCode import CQasm3Lexer
from parsing.GeneratedParsingCode import CQasm3Visitor
from src.TypeChecker import TypeChecker
from src.McKayDecomposer import McKayDecomposer
from src.SquirrelErrorHandler import SquirrelErrorHandler
from src.SquirrelASTCreator import SquirrelASTCreator
from src.TestInterpreter import TestInterpreter
from src.Replacer import Replacer
from src.Writer import Writer
import antlr4

class Circuit:
    def __init__(self, gates, cqasm3_string):
        """Create a circuit object from a cQasm3 string.

            * type-checking is performed, eliminating qubit indices errors and incoherences
            * checks that used gates are supported and mentioned in `gates` with appropriate signatures
            * does not support map or variables, and other things...
            * for example of `gates` dictionary, please look at TestGates.py
        """

        self.gates = gates

        input_stream = antlr4.InputStream(cqasm3_string)

        lexer = CQasm3Lexer.CQasm3Lexer(input_stream)

        stream = antlr4.CommonTokenStream(lexer)

        parser = CQasm3Parser.CQasm3Parser(stream)

        parser.removeErrorListeners()
        parser.addErrorListener(SquirrelErrorHandler())

        tree = parser.prog()

        typeChecker = TypeChecker(self.gates)
        typeChecker.visit(tree) # FIXME: return error instead of throwing?

        squirrelASTCreator = SquirrelASTCreator(self.gates)
        self.squirrelAST = squirrelASTCreator.visit(tree)

    
    def decompose_mckay(self):
        """Perform gate fusion on all one-qubit gates and decompose them in the McKay style.

            * all one-qubit gates on same qubit are merged together, without attempting to commute any gate
            * two-or-more-qubit gates are left as-is
            * merged one-qubit gates are decomposed according to McKay decomposition, that is:
                    gate   ---->    Rz.Rx(pi/2).Rz.Rx(pi/2).Rz
            * _global phase is deemed irrelevant_, therefore a simulator backend might produce different output
                for the input and output circuit - those outputs should be equivalent modulo global phase.
        """

        mcKayDecomposer = McKayDecomposer(self.gates)
        self.squirrelAST = mcKayDecomposer.process(self.squirrelAST)
    

    def replace(self, gateName, f):
        """Manually replace occurrences of a given gate with a list of gates.

            * this can be called decomposition - but it's the least fancy version of it
            * function parameter gives the decomposition based on parameters of original gate
        """

        assert gateName in self.gates, f"Cannot replace unknown gate `{gateName}`"
        replacer = Replacer(self.gates) # FIXME: only one instance of this is needed.
        self.squirrelAST = replacer.process(self.squirrelAST, gateName, f)


    def test_get_circuit_matrix(self):
        """Get the (large) unitary matrix corresponding to the circuit.

            * this matrix has 4**n elements, where n is the number of qubits
            * therefore this function is only here for testing purposes on small number of qubits
            * result is stored as a numpy array of complex numbers
        """

        interpreter = TestInterpreter(self.gates)
        return interpreter.process(self.squirrelAST)


    def __repr__(self):
        """Write the circuit to a cQasm3 string.

            * comments are removed
        """

        writer = Writer(self.gates)
        return writer.process(self.squirrelAST)