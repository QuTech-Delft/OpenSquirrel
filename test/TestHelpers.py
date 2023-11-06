from src.Common import ATOL
import numpy as np

def areMatricesEqualUpToGlobalPhase(matrixA, matrixB):
    firstNonZero = next((i, j) for i in range(matrixA.shape[0]) for j in range(matrixA.shape[1]) if abs(matrixA[i, j]) > ATOL)

    if abs(matrixB[firstNonZero]) < ATOL:
        return False

    phaseDifference = matrixA[firstNonZero] / matrixB[firstNonZero]

    return np.allclose(matrixA, phaseDifference * matrixB)
