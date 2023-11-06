from src.Common import ArgType
from src.Gates import querySignature

class Writer:
    def __init__(self, gates):
        self.gates = gates

    def process(self, squirrelAST):
        output = ""
        output += f'''version 3.0\n\nqubit[{squirrelAST.nQubits}] {squirrelAST.qubitRegisterName}\n\n'''

        for gateName, gateArgs in squirrelAST.operations:
            signature = querySignature(self.gates, gateName)

            args = [f"{squirrelAST.qubitRegisterName}[{arg}]" if t == ArgType.QUBIT else f"{arg}" for arg, t in zip(gateArgs, signature)]

            output += f"{gateName} {', '.join(args)}\n"
        
        return output
