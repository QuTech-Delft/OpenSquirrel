from opensquirrel.Common import ExprType, exprTypeToArgType
from opensquirrel.Gates import querySignature
from parsing.GeneratedParsingCode import CQasm3Visitor


class TypeChecker(CQasm3Visitor.CQasm3Visitor):
    def __init__(self, gates):
        self.gates = gates
        self.nQubits = 0

    def visitProg(self, ctx):
        self.visit(ctx.qubitRegisterDeclaration())
        for gate in ctx.gateApplication():
            self.visit(gate)

    def visitQubitRegisterDeclaration(self, ctx):
        self.nQubits = int(str(ctx.INT()))
        self.registerName = str(ctx.ID())

    def visitGateApplication(self, ctx):
        # Check that the type of operands match the gate declaration
        gateName = str(ctx.ID())
        if gateName not in self.gates:
            raise Exception(f"Unknown gate `{gateName}`")

        expectedSignature = querySignature(self.gates, gateName)

        if len(ctx.expr()) != len(expectedSignature):
            raise Exception(
                f"Gate `{gateName}` takes {len(expectedSignature)} arguments," f" but {len(ctx.expr())} were given!"
            )

        i = 0
        qubitArrays = None
        for arg in ctx.expr():
            argumentData = self.visit(arg)
            argumentType = argumentData[0]
            if argumentType == ExprType.QUBITREFS:
                if isinstance(qubitArrays, int) and qubitArrays != argumentData[1]:
                    raise Exception("Invalid gate call with qubit arguments of different sizes")

                qubitArrays = argumentData[1]

            if expectedSignature[i] != exprTypeToArgType(argumentType):
                raise Exception(
                    f"Argument #{i} passed to gate `{gateName}` is of type"
                    f" {exprTypeToArgType(argumentType)} but should be {expectedSignature[i]}"
                )
            i += 1

    def visitQubit(self, ctx):
        if str(ctx.ID()) != self.registerName:
            raise Exception(f"Qubit register {str(ctx.ID())} not declared")

        qubitIndex = int(str(ctx.INT()))
        if qubitIndex >= self.nQubits:
            raise Exception(f"Qubit index {qubitIndex} out of range")

        return (ExprType.QUBITREFS, 1)

    def visitQubits(self, ctx):
        if str(ctx.ID()) != self.registerName:
            raise Exception(f"Qubit register {str(ctx.ID())} not declared")

        qubitIndices = list(map(int, map(str, ctx.INT())))
        if any(i >= self.nQubits for i in qubitIndices):
            raise Exception(f"Qubit index {next(i for i in qubitIndices if i >= self.nQubits)} out of range")

        return ExprType.QUBITREFS, len(qubitIndices)

    def visitQubitRange(self, ctx):
        if str(ctx.ID()) != self.registerName:
            raise Exception(f"Qubit register {str(ctx.ID())} not declared")

        qubitIndex1 = int(str(ctx.INT(0)))
        qubitIndex2 = int(str(ctx.INT(1)))
        if max(qubitIndex1, qubitIndex2) >= self.nQubits:
            raise Exception(f"Qubit indices {qubitIndex1}:{qubitIndex2} out of range")

        if qubitIndex1 > qubitIndex2:
            raise Exception(f"Qubit indices {qubitIndex1}:{qubitIndex2} malformed")

        return (ExprType.QUBITREFS, qubitIndex2 - qubitIndex1 + 1)

    def visitIntLiteral(self, ctx):
        return (ExprType.INT,)

    def visitNegatedIntLiteral(self, ctx):
        return (ExprType.INT,)

    def visitFloatLiteral(self, ctx):
        return (ExprType.FLOAT,)

    def visitNegatedFloatLiteral(self, ctx):
        return (ExprType.FLOAT,)
