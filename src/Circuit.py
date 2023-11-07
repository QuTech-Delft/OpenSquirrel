from parsing.GeneratedParsingCode import CQasm3Parser
from parsing.GeneratedParsingCode import CQasm3Lexer
from parsing.GeneratedParsingCode import CQasm3Visitor
from src.TypeChecker import TypeChecker
from src.McKayDecomposer import McKayDecomposer
from src.SquirrelErrorHandler import SquirrelErrorHandler
from src.SquirrelAST import SquirrelAST
from src.SquirrelASTCreator import SquirrelASTCreator
from src.TestInterpreter import TestInterpreter
from src.Replacer import Replacer
from src.Writer import Writer
from test.TestGates import TEST_GATES as DefaultGates # For the doctest.
import antlr4

class Circuit:
    """The Circuit class is the only interface to access OpenSquirrel's features.

A Circuit object is constructed from a cQasm3 string, representing a quantum circuit, and a Python dictionary
containing the prototypes and semantic of the allowed quantum gates.
A default set of gates is exposed as `opensquirrel.DefaultGates` but it can be replaced and extended.

>>> c = Circuit.from_string(DefaultGates, "version 3.0; qubit[3] q; h q[0]")
>>> c
version 3.0
<BLANKLINE>
qubit[3] q
<BLANKLINE>
h q[0]
<BLANKLINE>
>>> c.decompose_mckay()
>>> c
version 3.0
<BLANKLINE>
qubit[3] q
<BLANKLINE>
x90 q[0]
rz q[0], 1.5707963267948966
x90 q[0]
<BLANKLINE>
"""

    def __init__(self, squirrelAST: SquirrelAST):
        """Create a circuit object from a SquirrelAST object."""

        self.gates = squirrelAST.gates
        self.squirrelAST = squirrelAST


    @classmethod
    def from_string(cls, gates, cqasm3_string):
        """Create a circuit object from a cQasm3 string. All the gates in the circuit need to be defined in the `gates` argument.

            * type-checking is performed, eliminating qubit indices errors and incoherences
            * checks that used gates are supported and mentioned in `gates` with appropriate signatures
            * does not support map or variables, and other things...
            * for example of `gates` dictionary, please look at TestGates.py
        """

        input_stream = antlr4.InputStream(cqasm3_string)

        lexer = CQasm3Lexer.CQasm3Lexer(input_stream)

        stream = antlr4.CommonTokenStream(lexer)

        parser = CQasm3Parser.CQasm3Parser(stream)

        parser.removeErrorListeners()
        parser.addErrorListener(SquirrelErrorHandler())

        tree = parser.prog()

        typeChecker = TypeChecker(gates)
        typeChecker.visit(tree) # FIXME: return error instead of throwing?

        squirrelASTCreator = SquirrelASTCreator(gates)

        return Circuit(squirrelASTCreator.visit(tree))

    
    def getNumberOfQubits(self):
        return self.squirrelAST.nQubits

    
    def getQubitRegisterName(self):
        return self.squirrelAST.qubitRegisterName

    
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