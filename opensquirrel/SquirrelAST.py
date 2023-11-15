from opensquirrel.Gates import querySignature


class SquirrelAST:
    # This is just a list of gates (for now?)
    def __init__(self, gates, nQubits, qubitRegisterName):
        self.gates = gates
        self.nQubits = nQubits
        self.operations = []
        self.qubitRegisterName = qubitRegisterName

    def addGate(self, gateName, *interpretedArgs):
        signature = querySignature(self.gates, gateName)
        assert len(signature) == len(interpretedArgs), f"Wrong number of arguments for gate `{gateName}`"

        # FIXME: Also check int vs float

        self.operations.append((gateName, interpretedArgs))

    def addComment(self, commentString: str):
        assert "*/" not in commentString, "Comment contains illegal characters"
        self.operations.append(commentString)

    def __eq__(self, other):
        if self.gates != other.gates:
            return False

        if self.nQubits != other.nQubits:
            return False

        if self.qubitRegisterName != other.qubitRegisterName:
            return False

        if len(self.operations) != len(other.operations):
            return False

        for i in range(len(self.operations)):
            leftName, leftArgs = self.operations[i]
            rightName, rightArgs = other.operations[i]

            if leftName != rightName:
                return False

            if len(leftArgs) != len(rightArgs) or any(leftArgs[i] != rightArgs[i] for i in range(len(leftArgs))):
                # if len(leftArgs) != len(rightArgs) or any(abs(leftArgs[i] - rightArgs[i]) >
                # ATOL for i in range(len(leftArgs))):
                return False

        return True

    def __repr__(self):
        return f"""AST ({self.nQubits} qubits, register {self.qubitRegisterName}): {self.operations}"""
