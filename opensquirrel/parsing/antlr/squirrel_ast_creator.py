from opensquirrel.common import ArgType
from opensquirrel.gates import querySignature
from opensquirrel.parsing.antlr.generated import CQasm3Visitor
from opensquirrel.squirrel_ast import SquirrelAST


class SquirrelASTCreator(CQasm3Visitor.CQasm3Visitor):
    def __init__(self, gates):
        self.gates = gates
        self.squirrel_ast = None

    def visitProg(self, ctx):
        qubit_register_name, number_of_qubits = self.visit(ctx.qubitRegisterDeclaration())  # Use?

        self.squirrel_ast = SquirrelAST(self.gates, number_of_qubits, qubit_register_name)

        for gate_application in ctx.gateApplication():
            self.visit(gate_application)

        return self.squirrel_ast

    def visitGateApplication(self, ctx):
        gate_name = str(ctx.ID())

        signature = querySignature(self.gates, gate_name)

        number_of_operands = next(
            len(self.visit(ctx.expr(i))) for i in range(len(signature)) if signature[i] == ArgType.QUBIT
        )

        expanded_args = [
            self.visit(ctx.expr(i))
            if signature[i] == ArgType.QUBIT
            else [self.visit(ctx.expr(i)) for _ in range(number_of_operands)]
            for i in range(len(signature))
        ]

        for individual_args in zip(*expanded_args):
            self.squirrel_ast.addGate(gate_name, *individual_args)

    def visitQubitRegisterDeclaration(self, ctx):
        return str(ctx.ID()), int(str(ctx.INT()))

    def visitQubit(self, ctx):
        return [int(str(ctx.INT()))]

    def visitQubits(self, ctx):
        return list(map(int, map(str, ctx.INT())))

    def visitQubitRange(self, ctx):
        qubit1 = int(str(ctx.INT(0)))
        qubit2 = int(str(ctx.INT(1)))
        return list(range(qubit1, qubit2 + 1))

    def visitFloatLiteral(self, ctx):
        return float(str(ctx.FLOAT()))

    def visitNegatedFloatLiteral(self, ctx):
        return -float(str(ctx.FLOAT()))

    def visitIntLiteral(self, ctx):
        return int(str(ctx.INT()))

    def visitNegatedIntLiteral(self, ctx):
        return -int(str(ctx.INT()))
