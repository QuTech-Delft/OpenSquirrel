import numpy as np

from opensquirrel.Common import Can1
from opensquirrel.Gates import MultiQubitMatrixSemantic, SingleQubitAxisAngleSemantic


# This should only be used for testing and on circuits with low number of qubits.
def getBigMatrix(semantic, qubitOperands, totalQubits):
    if isinstance(semantic, SingleQubitAxisAngleSemantic):
        whichQubit = qubitOperands[0]

        axis, angle, phase = semantic.axis, semantic.angle, semantic.phase
        result = np.kron(
            np.kron(np.eye(1 << (totalQubits - whichQubit - 1)), Can1(axis, angle, phase)), np.eye(1 << whichQubit)
        )
        assert result.shape == (1 << totalQubits, 1 << totalQubits)
        return result

    assert isinstance(semantic, MultiQubitMatrixSemantic)

    m = semantic.matrix

    assert m.shape[0] == 1 << len(qubitOperands)

    result = np.zeros((1 << totalQubits, 1 << totalQubits), dtype=np.complex128)

    for input in range(1 << totalQubits):
        smallMatrixCol = 0
        for i in range(len(qubitOperands)):
            smallMatrixCol |= ((input & (1 << qubitOperands[i])) >> qubitOperands[i]) << (len(qubitOperands) - 1 - i)

        col = m[:, smallMatrixCol]

        for output in range(len(col)):
            coeff = col[output]

            largeOutput = 0
            for i in range(len(qubitOperands)):
                index = len(qubitOperands) - i - 1
                largeOutput |= ((output & (1 << index)) >> index) << qubitOperands[i]

            result[largeOutput][input] = coeff

    return result
