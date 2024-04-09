import inspect

from opensquirrel.default_gates import default_gate_aliases, default_gate_set
from opensquirrel.default_measurements import default_measurement_aliases, default_measurement_set
from opensquirrel.operation_library import GateLibrary, MeasurementLibrary
from opensquirrel.parse.antlr.generated import CQasm3Visitor
from opensquirrel.squirrel_ir import Bit, Float, Int, Qubit, SquirrelIR


class SquirrelIRCreator(GateLibrary, MeasurementLibrary, CQasm3Visitor.CQasm3Visitor):
    """
    This class creates a SquirrelIR object from an ANTLR parse tree.
    It is an instance of the ANTLR abstract syntax tree visitor class.
    Therefore, method names are fixed and based on rule names in the Grammar .g4 file.
    """

    def __init__(
        self,
        gate_set=default_gate_set,
        gate_aliases=default_gate_aliases,
        measurement_set=default_measurement_set,
        measurement_aliases=default_measurement_aliases,
    ):
        GateLibrary.__init__(self, gate_set, gate_aliases)
        MeasurementLibrary.__init__(self, measurement_set, measurement_aliases)
        self.squirrel_ir = None

    def visitProg(self, ctx):
        number_of_qubits, qubit_register_name = self.visit(ctx.qubitRegisterDeclaration())

        self.squirrel_ir = SquirrelIR(number_of_qubits=number_of_qubits, qubit_register_name=qubit_register_name)

        for gate_application in ctx.gateApplication():
            self.visit(gate_application)

        return self.squirrel_ir

    def visitGateApplication(self, ctx):
        gate_name = str(ctx.ID())

        generator_f = GateLibrary.get_gate_f(self, gate_name)
        parameters = inspect.signature(generator_f).parameters

        number_of_operands = next(
            len(self.visit(ctx.expr(i))) for i, par in enumerate(parameters.values()) if par.annotation == Qubit
        )

        # The below is for handling e.g. `cr q[1:3], q[5:7], 1.23`
        expanded_args = [
            self.visit(ctx.expr(i)) if par.annotation == Qubit else [self.visit(ctx.expr(i))] * number_of_operands
            for i, par in enumerate(parameters.values())
        ]

        for individual_args in zip(*expanded_args):
            self.squirrel_ir.add_gate(generator_f(*individual_args))

    def visitMeasurementApplication(self, ctx):
        measurement_name = str(ctx.ID())

        generator_f = MeasurementLibrary.get_measurement_f(self, measurement_name)
        parameters = inspect.signature(generator_f).parameters

        number_of_operands = next(
            len(self.visit(ctx.expr(i))) for i, par in enumerate(parameters.values()) if par.annotation == Qubit
        )

        # The below is for handling e.g. `cr q[1:3], q[5:7], 1.23`
        expanded_args = [
            self.visit(ctx.expr(i)) if par.annotation == Qubit else [self.visit(ctx.expr(i))] * number_of_operands
            for i, par in enumerate(parameters.values())
        ]

        for individual_args in zip(*expanded_args):
            self.squirrel_ir.add_measurement(generator_f(*individual_args))

    def visitQubitRegisterDeclaration(self, ctx):
        return int(str(ctx.INT())), str(ctx.ID())

    def visitQubit(self, ctx):
        return [Qubit(int(str(ctx.INT())))]

    def visitBit(self, ctx):
        return [Bit(int(str(ctx.INT())))]

    def visitQubits(self, ctx):
        return list(map(Qubit, map(int, map(str, ctx.INT()))))

    def visitBits(self, ctx):
        return list(map(Bit, map(int, map(str, ctx.INT()))))

    def visitQubitRange(self, ctx):
        first_qubit_index = int(str(ctx.INT(0)))
        last_qubit_index = int(str(ctx.INT(1)))
        return list(map(Qubit, range(first_qubit_index, last_qubit_index + 1)))

    def visitBitRange(self, ctx):
        first_bit_index = int(str(ctx.INT(0)))
        last_bit_index = int(str(ctx.INT(1)))
        return list(map(Bit, range(first_bit_index, last_bit_index + 1)))

    def visitFloatLiteral(self, ctx):
        return Float(float(str(ctx.FLOAT())))

    def visitNegatedFloatLiteral(self, ctx):
        return Float(-float(str(ctx.FLOAT())))

    def visitIntLiteral(self, ctx):
        return Int(int(str(ctx.INT())))

    def visitNegatedIntLiteral(self, ctx):
        return Int(-int(str(ctx.INT())))
