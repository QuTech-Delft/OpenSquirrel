# Generated from CQasm3.g4 by ANTLR 4.13.1
from antlr4 import *
if "." in __name__:
    from .CQasm3Parser import CQasm3Parser
else:
    from CQasm3Parser import CQasm3Parser

# This class defines a complete generic visitor for a parse tree produced by CQasm3Parser.

class CQasm3Visitor(ParseTreeVisitor):

    # Visit a parse tree produced by CQasm3Parser#stateSep.
    def visitStateSep(self, ctx:CQasm3Parser.StateSepContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CQasm3Parser#prog.
    def visitProg(self, ctx:CQasm3Parser.ProgContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CQasm3Parser#qubitRegisterDeclaration.
    def visitQubitRegisterDeclaration(self, ctx:CQasm3Parser.QubitRegisterDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CQasm3Parser#gateApplication.
    def visitGateApplication(self, ctx:CQasm3Parser.GateApplicationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CQasm3Parser#Qubit.
    def visitQubit(self, ctx:CQasm3Parser.QubitContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CQasm3Parser#Qubits.
    def visitQubits(self, ctx:CQasm3Parser.QubitsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CQasm3Parser#QubitRange.
    def visitQubitRange(self, ctx:CQasm3Parser.QubitRangeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CQasm3Parser#IntLiteral.
    def visitIntLiteral(self, ctx:CQasm3Parser.IntLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CQasm3Parser#NegatedIntLiteral.
    def visitNegatedIntLiteral(self, ctx:CQasm3Parser.NegatedIntLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CQasm3Parser#FloatLiteral.
    def visitFloatLiteral(self, ctx:CQasm3Parser.FloatLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CQasm3Parser#NegatedFloatLiteral.
    def visitNegatedFloatLiteral(self, ctx:CQasm3Parser.NegatedFloatLiteralContext):
        return self.visitChildren(ctx)



del CQasm3Parser