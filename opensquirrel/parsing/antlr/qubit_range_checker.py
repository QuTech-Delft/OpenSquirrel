from opensquirrel.parsing.antlr.generated import CQasm3Visitor


class QubitRangeChecker(CQasm3Visitor.CQasm3Visitor):
    """
    This class checks that all qubit indices make sense in an ANTLR parse tree.
    It is an instance of the ANTLR abstract syntax tree visitor class.
    Therefore, method names are fixed and based on rule names in the Grammar .g4 file.
    """

    def __init__(self):
        self.number_of_qubits = 0

    def visitProg(self, ctx):
        self.visit(ctx.qubitRegisterDeclaration())
        for gate_application in ctx.gateApplication():
            self.visit(gate_application)

    def visitQubitRegisterDeclaration(self, ctx):
        self.number_of_qubits = int(str(ctx.INT()))

    def visitGateApplication(self, ctx):
        visited_args = (self.visit(arg) for arg in ctx.expr())
        qubit_argument_sizes = [qubit_range_size for qubit_range_size in visited_args if qubit_range_size is not None]

        if len(qubit_argument_sizes) > 0 and not all(s == qubit_argument_sizes[0] for s in qubit_argument_sizes):
            raise Exception("Invalid gate call with qubit arguments of different sizes")

    def visitMeasurementApplication(self, ctx):
        visited_args = (self.visit(arg) for arg in ctx.expr())
        qubit_argument_sizes = [qubit_range_size for qubit_range_size in visited_args if qubit_range_size is not None]

        if len(qubit_argument_sizes) > 0 and not all(s == qubit_argument_sizes[0] for s in qubit_argument_sizes):
            raise Exception("Invalid gate call with qubit arguments of different sizes")

    def visitQubit(self, ctx):
        qubit_index = int(str(ctx.INT()))
        if qubit_index >= self.number_of_qubits:
            raise Exception(f"Qubit index {qubit_index} out of range")

        return 1

    def visitQubits(self, ctx):
        qubit_indices = list(map(int, map(str, ctx.INT())))
        for qubit_index in qubit_indices:
            if qubit_index >= self.number_of_qubits:
                raise Exception(f"Qubit index {qubit_index} out of range")

        return len(qubit_indices)

    def visitQubitRange(self, ctx):
        first_qubit_index = int(str(ctx.INT(0)))
        last_qubit_index = int(str(ctx.INT(1)))

        if first_qubit_index > last_qubit_index:
            raise Exception(f"Qubit index range {first_qubit_index}:{last_qubit_index} malformed")

        if max(first_qubit_index, last_qubit_index) >= self.number_of_qubits:
            raise Exception(f"Qubit index range {first_qubit_index}:{last_qubit_index} out of range")

        return last_qubit_index - first_qubit_index + 1

    def visitIntLiteral(self, ctx):
        return None

    def visitNegatedIntLiteral(self, ctx):
        return None

    def visitFloatLiteral(self, ctx):
        return None

    def visitNegatedFloatLiteral(self, ctx):
        return None
