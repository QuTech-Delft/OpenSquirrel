from opensquirrel.common import ArgType
from opensquirrel.gates import querySignature


class Writer:
    NUMBER_OF_SIGNIFICANT_DIGITS = 8

    def __init__(self, gates):
        self.gates = gates

    @classmethod
    def _format_arg(cls, squirrelAST, arg, t: ArgType):
        if t == ArgType.QUBIT:
            return f"{squirrelAST.qubitRegisterName}[{arg}]"
        if t == ArgType.INT:
            return f"{int(arg)}"
        if t == ArgType.FLOAT:
            return f"{float(arg):.{Writer.NUMBER_OF_SIGNIFICANT_DIGITS}}"

        assert False, "Unknown argument type"

    def process(self, squirrelAST):
        output = ""
        output += f"""version 3.0\n\nqubit[{squirrelAST.nQubits}] {squirrelAST.qubitRegisterName}\n\n"""

        for operation in squirrelAST.operations:
            if isinstance(operation, str):
                comment = operation
                assert "*/" not in comment, "Comment contains illegal characters"

                output += f"\n/* {comment} */\n\n"
                continue

            gateName, gateArgs = operation
            signature = querySignature(self.gates, gateName)

            args = [Writer._format_arg(squirrelAST, arg, t) for arg, t in zip(gateArgs, signature)]

            output += f"{gateName} {', '.join(args)}\n"

        return output
