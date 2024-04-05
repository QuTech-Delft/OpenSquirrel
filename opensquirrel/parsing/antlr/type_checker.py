import inspect

from opensquirrel.default_gates import default_gate_aliases, default_gate_set
from opensquirrel.default_measurements import default_measurement_aliases, default_measurement_set
from opensquirrel.operation_library import GateLibrary, MeasurementLibrary
from opensquirrel.parsing.antlr.generated import CQasm3Visitor
from opensquirrel.squirrel_ir import Float, Int, Qubit, Bit


class TypeChecker(GateLibrary, MeasurementLibrary, CQasm3Visitor.CQasm3Visitor):
    """
    This class checks that all gate parameter types make sense in an ANTLR parse tree.
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
        self.qubit_register_name = None
        self.bit_register_name = None

    def visitProg(self, ctx):
        self.visit(ctx.qubitRegisterDeclaration())
        for gate_application in ctx.gateApplication():
            self.visit(gate_application)

    def visitQubitRegisterDeclaration(self, ctx):
        self.qubit_register_name = str(ctx.ID())

    def visitBitRegisterDeclaration(self, ctx):
        self.bit_register_name = str(ctx.ID())

    def visitGateApplication(self, ctx):
        # Check that the types of the operands match the gate generator function.
        gate_name = str(ctx.ID())
        generator_f = GateLibrary.get_gate_f(self, gate_name)

        parameters = inspect.signature(generator_f).parameters

        if len(ctx.expr()) > len(parameters):
            raise Exception(f"Gate `{gate_name}` takes {len(parameters)} arguments, but {len(ctx.expr())} were given!")

        for i, param in enumerate(parameters.values()):
            actual_type = self.visit(ctx.expr(i))
            expected_type = param.annotation
            if actual_type != expected_type:
                raise Exception(
                    f"Argument #{i} passed to gate `{gate_name}` is of type"
                    f" {actual_type} but should be {expected_type}"
                )

    def visitMeasurementApplication(self, ctx):
        # Check that the types of the operands match the measurement generator function.
        measurement_name = str(ctx.ID())
        generator_f = MeasurementLibrary.get_measurement_f(self, measurement_name)

        parameters = inspect.signature(generator_f).parameters

        if len(ctx.expr()) > len(parameters):
            raise Exception(
                f"Measurement `{measurement_name}` takes {len(parameters)} arguments, but {len(ctx.expr())} were given!"
            )

        for i, param in enumerate(parameters.values()):
            actual_type = self.visit(ctx.expr(i))
            expected_type = param.annotation
            if actual_type != expected_type:
                raise Exception(
                    f"Argument #{i} passed to measurement `{measurement_name}` is of type"
                    f" {actual_type} but should be {expected_type}"
                )

    def visitQubit(self, ctx):
        if str(ctx.ID()) != self.qubit_register_name:
            raise Exception(f"Qubit register {str(ctx.ID())} not declared")

        return Qubit

    def visitBit(self, ctx):
        if str(ctx.ID()) != self.bit_register_name:
            raise Exception(f"Classical bit register {str(ctx.ID())} not declared")

        return Bit

    def visitQubits(self, ctx):
        if str(ctx.ID()) != self.qubit_register_name:
            raise Exception(f"Qubit register {str(ctx.ID())} not declared")

        return Qubit

    def visitBits(self, ctx):
        if str(ctx.ID()) != self.bit_register_name:
            raise Exception(f"Classical bit register {str(ctx.ID())} not declared")

        return Bit

    def visitQubitRange(self, ctx):
        if str(ctx.ID()) != self.qubit_register_name:
            raise Exception(f"Qubit register {str(ctx.ID())} not declared")

        return Qubit

    def visitBitRange(self, ctx):
        if str(ctx.ID()) != self.bit_register_name:
            raise Exception(f"Bit register {str(ctx.ID())} not declared")

        return Bit

    def visitIntLiteral(self, ctx):
        return Int

    def visitNegatedIntLiteral(self, ctx):
        return Int

    def visitFloatLiteral(self, ctx):
        return Float

    def visitNegatedFloatLiteral(self, ctx):
        return Float
