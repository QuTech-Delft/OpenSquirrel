from opensquirrel.common import ArgType
from opensquirrel.gates import querySignature
from opensquirrel.squirrel_ast import SquirrelAST


class Replacer:
    def __init__(self, gates):
        self.gates = gates

    def process(self, squirrelAST: SquirrelAST, replacedGateName: str, f):
        result = SquirrelAST(self.gates, squirrelAST.nQubits, squirrelAST.qubitRegisterName)

        signature = querySignature(self.gates, replacedGateName)

        for operation in squirrelAST.operations:
            if isinstance(operation, str):
                continue

            otherGateName, otherArgs = operation

            if otherGateName != replacedGateName:
                result.addGate(otherGateName, *otherArgs)
                continue

            # FIXME: handle case where if f is not a function but directly a list.

            assert len(otherArgs) == len(signature)
            originalQubits = set(otherArgs[i] for i in range(len(otherArgs)) if signature[i] == ArgType.QUBIT)

            replacement = f(*otherArgs)

            # TODO: Here, check that the semantic of the replacement is the same!
            # For this, need to update the simulation capabilities.

            # TODO: Do we allow skipping the replacement, based on arguments?

            assert isinstance(replacement, list), "Substitution needs to be a list"

            for replacementGate in replacement:
                replacementGateName, replacementGateArgs = replacementGate

                replacementGateSignature = querySignature(self.gates, replacementGateName)
                assert len(replacementGateArgs) == len(replacementGateSignature)
                assert all(
                    replacementGateArgs[i] in originalQubits
                    for i in range(len(replacementGateArgs))
                    if replacementGateSignature[i] == ArgType.QUBIT
                ), (f"Substitution for gate `{replacedGateName}` " f"must use the input qubits {originalQubits} only")

                result.addGate(replacementGateName, *replacementGateArgs)

        return result
