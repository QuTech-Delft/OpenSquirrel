from opensquirrel.Common import ArgType
from opensquirrel.Gates import querySignature


class Writer:
    def __init__(self, gates):
        self.gates = gates

    def process(self, squirrelAST):
        output = ""
        output += f'''version 3.0\n\nqubit[{squirrelAST.nQubits}] {squirrelAST.qubitRegisterName}\n\n'''

        for operation in squirrelAST.operations:
            if isinstance(operation, str):
                comment = operation
                assert "*/" not in comment, "Comment contains illegal characters"

                output += f"\n/* {comment} */\n\n"
                continue
            
            gateName, gateArgs = operation
            signature = querySignature(self.gates, gateName)

            args = [f"{squirrelAST.qubitRegisterName}[{arg}]"
                    if t == ArgType.QUBIT else f"{arg}" for arg, t in zip(gateArgs, signature)]

            output += f"{gateName} {', '.join(args)}\n"
        
        return output
