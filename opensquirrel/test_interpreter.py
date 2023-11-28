import numpy as np

from opensquirrel.common import ArgType
from opensquirrel.gates import querySemantic, querySignature
from opensquirrel.utils.matrix_expander import get_expanded_matrix


class TestInterpreter:
    def __init__(self, gates):
        self.gates = gates

    def process(self, squirrelAST):
        totalUnitary = np.eye(1 << squirrelAST.nQubits, dtype=np.complex128)

        for operation in squirrelAST.operations:
            if isinstance(operation, str):
                continue

            gateName, gateArgs = operation

            signature = querySignature(self.gates, gateName)
            assert len(gateArgs) == len(signature)
            qubitOperands = [gateArgs[i] for i in range(len(gateArgs)) if signature[i] == ArgType.QUBIT]
            semantic = querySemantic(
                self.gates, gateName, *[gateArgs[i] for i in range(len(gateArgs)) if signature[i] != ArgType.QUBIT]
            )
            bigMatrix = get_expanded_matrix(semantic, qubitOperands, total_qubits=squirrelAST.nQubits)
            totalUnitary = bigMatrix @ totalUnitary

        return totalUnitary
