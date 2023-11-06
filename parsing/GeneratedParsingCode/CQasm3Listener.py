# Generated from CQasm3.g4 by ANTLR 4.13.1
from antlr4 import *
if "." in __name__:
    from .CQasm3Parser import CQasm3Parser
else:
    from CQasm3Parser import CQasm3Parser

# This class defines a complete listener for a parse tree produced by CQasm3Parser.
class CQasm3Listener(ParseTreeListener):

    # Enter a parse tree produced by CQasm3Parser#stateSep.
    def enterStateSep(self, ctx:CQasm3Parser.StateSepContext):
        pass

    # Exit a parse tree produced by CQasm3Parser#stateSep.
    def exitStateSep(self, ctx:CQasm3Parser.StateSepContext):
        pass


    # Enter a parse tree produced by CQasm3Parser#prog.
    def enterProg(self, ctx:CQasm3Parser.ProgContext):
        pass

    # Exit a parse tree produced by CQasm3Parser#prog.
    def exitProg(self, ctx:CQasm3Parser.ProgContext):
        pass


    # Enter a parse tree produced by CQasm3Parser#qubitRegisterDeclaration.
    def enterQubitRegisterDeclaration(self, ctx:CQasm3Parser.QubitRegisterDeclarationContext):
        pass

    # Exit a parse tree produced by CQasm3Parser#qubitRegisterDeclaration.
    def exitQubitRegisterDeclaration(self, ctx:CQasm3Parser.QubitRegisterDeclarationContext):
        pass


    # Enter a parse tree produced by CQasm3Parser#gateApplication.
    def enterGateApplication(self, ctx:CQasm3Parser.GateApplicationContext):
        pass

    # Exit a parse tree produced by CQasm3Parser#gateApplication.
    def exitGateApplication(self, ctx:CQasm3Parser.GateApplicationContext):
        pass


    # Enter a parse tree produced by CQasm3Parser#Qubit.
    def enterQubit(self, ctx:CQasm3Parser.QubitContext):
        pass

    # Exit a parse tree produced by CQasm3Parser#Qubit.
    def exitQubit(self, ctx:CQasm3Parser.QubitContext):
        pass


    # Enter a parse tree produced by CQasm3Parser#Qubits.
    def enterQubits(self, ctx:CQasm3Parser.QubitsContext):
        pass

    # Exit a parse tree produced by CQasm3Parser#Qubits.
    def exitQubits(self, ctx:CQasm3Parser.QubitsContext):
        pass


    # Enter a parse tree produced by CQasm3Parser#QubitRange.
    def enterQubitRange(self, ctx:CQasm3Parser.QubitRangeContext):
        pass

    # Exit a parse tree produced by CQasm3Parser#QubitRange.
    def exitQubitRange(self, ctx:CQasm3Parser.QubitRangeContext):
        pass


    # Enter a parse tree produced by CQasm3Parser#IntLiteral.
    def enterIntLiteral(self, ctx:CQasm3Parser.IntLiteralContext):
        pass

    # Exit a parse tree produced by CQasm3Parser#IntLiteral.
    def exitIntLiteral(self, ctx:CQasm3Parser.IntLiteralContext):
        pass


    # Enter a parse tree produced by CQasm3Parser#NegatedIntLiteral.
    def enterNegatedIntLiteral(self, ctx:CQasm3Parser.NegatedIntLiteralContext):
        pass

    # Exit a parse tree produced by CQasm3Parser#NegatedIntLiteral.
    def exitNegatedIntLiteral(self, ctx:CQasm3Parser.NegatedIntLiteralContext):
        pass


    # Enter a parse tree produced by CQasm3Parser#FloatLiteral.
    def enterFloatLiteral(self, ctx:CQasm3Parser.FloatLiteralContext):
        pass

    # Exit a parse tree produced by CQasm3Parser#FloatLiteral.
    def exitFloatLiteral(self, ctx:CQasm3Parser.FloatLiteralContext):
        pass


    # Enter a parse tree produced by CQasm3Parser#NegatedFloatLiteral.
    def enterNegatedFloatLiteral(self, ctx:CQasm3Parser.NegatedFloatLiteralContext):
        pass

    # Exit a parse tree produced by CQasm3Parser#NegatedFloatLiteral.
    def exitNegatedFloatLiteral(self, ctx:CQasm3Parser.NegatedFloatLiteralContext):
        pass



del CQasm3Parser