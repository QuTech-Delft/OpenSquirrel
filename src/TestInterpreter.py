from src.Common import ArgType
from src.MatrixExpander import getBigMatrix
from src.Gates import querySignature, querySemantic
import numpy as np

class TestInterpreter:
  def __init__(self, gates):
    self.gates = gates

  def process(self, squirrelAST):
    totalUnitary = np.eye(1 << squirrelAST.nQubits, dtype=np.complex128)

    for gateName, gateArgs in squirrelAST.operations:
      signature = querySignature(self.gates, gateName)
      assert len(gateArgs) == len(signature)
      qubitOperands = [gateArgs[i] for i in range(len(gateArgs)) if signature[i] == ArgType.QUBIT]
      semantic = querySemantic(self.gates, gateName, *[gateArgs[i] for i in range(len(gateArgs)) if signature[i] != ArgType.QUBIT])
      bigMatrix = getBigMatrix(semantic, qubitOperands, totalQubits = squirrelAST.nQubits)
      totalUnitary = bigMatrix @ totalUnitary
    
    return totalUnitary
