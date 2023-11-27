from opensquirrel.common import ArgType
from opensquirrel.gates import querySignature
from opensquirrel.squirrel_ast import SquirrelAST
from parsing.GeneratedParsingCode import CQasm3Visitor


class SquirrelASTCreator(CQasm3Visitor.CQasm3Visitor):
    def __init__(self, gates):
        self.gates = gates

    def visitProg(self, ctx):
        qubitRegisterName, nQubits = self.visit(ctx.qubitRegisterDeclaration())  # Use?

        self.squirrelAST = SquirrelAST(self.gates, nQubits, qubitRegisterName)

        for gApp in ctx.gateApplication():
            self.visit(gApp)

        return self.squirrelAST

    def visitGateApplication(self, ctx):
        gateName = str(ctx.ID())

        signature = querySignature(self.gates, gateName)

        numberOfQubits = next(
            len(self.visit(ctx.expr(i))) for i in range(len(signature)) if signature[i] == ArgType.QUBIT
        )

        expandedArgs = [
            self.visit(ctx.expr(i))
            if signature[i] == ArgType.QUBIT
            else [self.visit(ctx.expr(i)) for _ in range(numberOfQubits)]
            for i in range(len(signature))
        ]

        for individualArgs in zip(*expandedArgs):
            self.squirrelAST.addGate(gateName, *individualArgs)

    def visitQubitRegisterDeclaration(self, ctx):
        return str(ctx.ID()), int(str(ctx.INT()))

    def visitQubit(self, ctx):
        return [int(str(ctx.INT()))]

    def visitQubits(self, ctx):
        return list(map(int, map(str, ctx.INT())))

    def visitQubitRange(self, ctx):
        qubitIndex1 = int(str(ctx.INT(0)))
        qubitIndex2 = int(str(ctx.INT(1)))
        return list(range(qubitIndex1, qubitIndex2 + 1))

    def visitFloatLiteral(self, ctx):
        return float(str(ctx.FLOAT()))

    def visitNegatedFloatLiteral(self, ctx):
        return -float(str(ctx.FLOAT()))

    def visitIntLiteral(self, ctx):
        return int(str(ctx.INT()))

    def visitNegatedIntLiteral(self, ctx):
        return -int(str(ctx.INT()))
