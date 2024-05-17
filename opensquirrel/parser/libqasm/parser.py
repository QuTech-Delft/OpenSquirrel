import inspect
import itertools

import cqasm.v3x as cqasm

from opensquirrel.circuit import Circuit
from opensquirrel.default_gates import default_gate_aliases, default_gate_set
from opensquirrel.default_measurements import default_measurement_set
from opensquirrel.instruction_library import GateLibrary, MeasurementLibrary
from opensquirrel.register_manager import RegisterManager
from opensquirrel.squirrel_ir import Float, Int, Qubit, SquirrelIR

_ast_type_to_ir_type = {
    cqasm.types.QubitArray: Qubit,
    cqasm.values.ConstInt: Int,
    cqasm.values.ConstFloat: Float,
}


class Parser(GateLibrary, MeasurementLibrary):
    def __init__(
        self,
        gate_set=default_gate_set,
        gate_aliases=default_gate_aliases,
        measurement_set=default_measurement_set,
    ):
        GateLibrary.__init__(self, gate_set, gate_aliases)
        MeasurementLibrary.__init__(self, measurement_set)
        self.squirrel_ir = None

    @staticmethod
    def _get_qubits(ast_qubit_expression):
        ret = []
        if isinstance(ast_qubit_expression, cqasm.values.VariableRef):
            ret = [Qubit(index) for index in register_manager.get_qubit_range(ast_qubit_expression.variable.name)]
        if isinstance(ast_qubit_expression, cqasm.IndexRef):
            ret = [Qubit(index) for index in register_manager.get_qubit_indices(ast_qubit_expression.variable.name, ast_qubit_expression.indices)]
        return ret

    @staticmethod
    def _get_literal(cqasm_literal_expression):
        assert type(cqasm_literal_expression) in [cqasm.values.ConstInt, cqasm.values.ConstFloat]

        if isinstance(cqasm_literal_expression, cqasm.values.ConstInt):
            return Int(cqasm_literal_expression.value)

        if isinstance(cqasm_literal_expression, cqasm.values.ConstFloat):
            return Float(cqasm_literal_expression.value)

        return None

    @staticmethod
    def _check_ast_type(ast_expression, expected_ir_type):
        ast_type = (
            type(ast_expression.variable.typ)
            if isinstance(ast_expression, cqasm.values.IndexRef)
            else type(ast_expression)
        )

        # The check below is already guaranteed by libqasm, therefore it's just an assert.
        assert _ast_type_to_ir_type[ast_type] == expected_ir_type

    @classmethod
    def _get_expanded_statement_args(cls, generator_f, ast_args):
        parameters = inspect.signature(generator_f).parameters.values()

        ### The check below is already guaranteed by libqasm, therefore it's just an assert.
        assert len(parameters) == len(ast_args)
        for ast_arg, expected_parameter in zip(ast_args, parameters):
            cls._check_ast_type(ast_expression=ast_arg, expected_ir_type=expected_parameter.annotation)

        number_of_operands = next(
            len(ast_arg.indices)
            for ast_arg, expected_parameter in zip(ast_args, parameters)
            if expected_parameter.annotation == Qubit
        )

        expanded_args = [
            (
                cls._get_qubits(ast_arg) if expected_parameter.annotation == Qubit
                else [cls._get_literal(ast_arg)] * number_of_operands if not expected_parameter.annotation == Bit
                else None
            )
            for ast_arg, expected_parameter in zip(ast_args, parameters)
        ]

        return zip(*expanded_args)

    @staticmethod
    def _get_cqasm_param_type_letters(squirrel_type):
        if squirrel_type == Qubit:
            return "Q", "V"  # "V" is to allow array notations like q[3, 5, 7] and q[3:6]

        if squirrel_type == Bit:
            return "B", "W"  # "W" is to allow array notations like b[3, 5, 7] and b[3:6]

        if squirrel_type == Float:
            return "f"

        if squirrel_type == Int:
            return "i"

        raise TypeError("Unsupported type")

    def _create_analyzer(self):
        without_defaults = True
        analyzer = cqasm.Analyzer("3.0", without_defaults)
        for generator_f in self.gate_set:
            for set_of_letters in itertools.product(
                *(
                    self._get_cqasm_param_type_letters(p.annotation)
                    for p in inspect.signature(generator_f).parameters.values()
                )
            ):
                param_types = "".join(set_of_letters)
                analyzer.register_instruction(generator_f.__name__, param_types)

        for generator_f in self.measurement_set:
            for set_of_letters in itertools.product(
                *(
                    self._get_cqasm_param_type_letters(p.annotation)
                    for p in inspect.signature(generator_f).parameters.values()
                )
            ):
                param_types = "".join(set_of_letters)
                analyzer.register_instruction(generator_f.__name__, param_types)

        return analyzer

    @staticmethod
    def _check_analysis_result(result):
        if isinstance(result, list):
            raise Exception("Parsing error: " + ", ".join(result))

    @staticmethod
    def _parse_ast_string(string):
        # FIXME: libqasm should return bytes, not the __repr__ of a bytes object ("b'q'")
        return string[2:-1]

    def circuit_from_string(self, s: str):
        # Analysis result will be either an Abstract Syntax Tree (AST) or a list of error messages
        analyzer = self._create_analyzer()
        analysis_result = analyzer.analyze_string(s)
        Parser._check_analysis_result(analysis_result)
        ast = analysis_result

        # Create RegisterManager
        register_manager = RegisterManager(ast)

        # Parse statements
        squirrel_ir = SquirrelIR()
        for statement in ast.block.statements:
            statement_name =  parse_ast_string_(statement.name)
            if "measure" in statement_name:
                generator_f = self.get_measurement_f(statement_name)
            else:
                generator_f = self.get_gate_f(statement_name)
            expanded_args = Parser._get_expanded_statement_args(generator_f, statement.operands)
            for arg_set in expanded_args:
                squirrel_ir.add_gate(generator_f(*arg_set))

        return Circuit(register_manager, squirrel_ir)
