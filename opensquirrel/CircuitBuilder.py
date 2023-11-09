from opensquirrel.Circuit import Circuit
from opensquirrel.SquirrelAST import SquirrelAST


class CircuitBuilder:
    """A class using the builder pattern to make construction of circuits easy.
    Adds corresponding gate when a method is called. Checks gates are known and called with the right arguments.
    Mainly here to allow for Qiskit-style circuit construction:

    >>> myCircuit = CircuitBuilder(DefaultGates, 3).h(0).cnot(0, 1).cnot(0, 2).to_circuit()

    """

    __default_qubit_register_name = "q"

    def __init__(self, gates, numberOfQubits):
        self.squirrelAST = SquirrelAST(gates, numberOfQubits, self.__default_qubit_register_name)

    def __getattr__(self, attr):
        def addComment(commentString: str):
            self.squirrelAST.addComment(commentString)
            return self
        
        def addThisGate(*args):
            self.squirrelAST.addGate(attr, *args)
            return self
        
        return addComment if attr == "comment" else addThisGate

    def to_circuit(self):
        return Circuit(self.squirrelAST)
