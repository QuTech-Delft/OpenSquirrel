import inspect
import itertools

import cqasm.v3x as cqasm

from opensquirrel.circuit import Circuit
from opensquirrel.default_gates import default_gate_aliases, default_gate_set
from opensquirrel.default_measurements import default_measurement_set
from opensquirrel.instruction_library import GateLibrary, MeasurementLibrary
from opensquirrel.register_manager import RegisterManager
from opensquirrel.squirrel_ir import Float, Int, Qubit, SquirrelIR


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
    def _parse_ast_string(string):
        # FIXME: libqasm should return bytes, not the __repr__ of a bytes object ("b'q'")
        return string[2:-1]

    @staticmethod
    def _ast_literal_to_ir_literal(cqasm_literal_expression):
        assert type(cqasm_literal_expression) in [cqasm.values.ConstInt, cqasm.values.ConstFloat]
        if isinstance(cqasm_literal_expression, cqasm.values.ConstInt):
            return Int(cqasm_literal_expression.value)
        if isinstance(cqasm_literal_expression, cqasm.values.ConstFloat):
            return Float(cqasm_literal_expression.value)
        return None

    @staticmethod
    def _type_of(ast_expression):
        if isinstance(ast_expression, cqasm.values.IndexRef) or isinstance(ast_expression, cqasm.values.VariableRef):
            return type(ast_expression.variable.typ)
        else:
            return type(ast_expression)

    @staticmethod
    def _size_of(ast_expression) -> int:
        if isinstance(ast_expression, cqasm.values.IndexRef):
            return len(ast_expression.indices)
        elif isinstance(ast_expression, cqasm.values.VariableRef):
            return int(ast_expression.variable.typ.size)
        else:
            return 1

    @staticmethod
    def _is_qubit_type(ast_expression):
        ast_type = Parser._type_of(ast_expression)
        return ast_type == cqasm.types.Qubit or ast_type == cqasm.types.QubitArray

    @staticmethod
    def _is_bit_type(ast_expression):
        ast_type = Parser._type_of(ast_expression)
        return ast_type == cqasm.types.Bit or ast_type == cqasm.types.BitArray

    @staticmethod
    def _get_qubits(ast_qubit_expression, register_manager):
        ret = []
        variable_name = Parser._parse_ast_string(ast_qubit_expression.variable.name)
        if isinstance(ast_qubit_expression, cqasm.values.VariableRef):
            qubit_range = register_manager.get_qubit_range(variable_name)
            ret = [Qubit(index) for index in range(qubit_range.first, qubit_range.first + qubit_range.size)]
        if isinstance(ast_qubit_expression, cqasm.values.IndexRef):
            indices = [int(i.value) for i in ast_qubit_expression.indices]
            ret = [Qubit(index) for index in register_manager.get_qubit_indices(variable_name, indices)]
        return ret

    @classmethod
    def _get_expanded_statement_args(cls, ast_args, register_manager):
        number_of_operands = 0
        for ast_arg in ast_args:
            if Parser._is_qubit_type(ast_arg):
                number_of_operands += Parser._size_of(ast_arg)
        expanded_args = []
        for ast_arg in ast_args:
            if Parser._is_qubit_type(ast_arg):
                expanded_args.append(cls._get_qubits(ast_arg, register_manager))
            elif not Parser._is_bit_type(ast_arg):
                expanded_args.append([cls._ast_literal_to_ir_literal(ast_arg)] * number_of_operands)
            else:  # Bit type
                pass
        return zip(*expanded_args)

    @staticmethod
    def _get_cqasm_param_type_letters(squirrel_type):
        if squirrel_type == Qubit:
            return "Q", "V"  # "V" is to allow array notations like q[3, 5, 7] and q[3:6]

        if squirrel_type == Float:
            return "f"

        if squirrel_type == Int:
            return "i"

        raise TypeError("Unsupported type")

    def _create_analyzer(self):
        # TODO: we are temporarily using the default analyzer,
        # mainly because there is a misalignment between the AST and the IR measure nodes
        # The AST currently produces measure nodes with a bit argument,
        # but the IR doesn't consider yet that bit argument
        # In the future, we may want to go back to no using the default analyzer again,
        # so that all gates are registered based on OpenSquirrel's default gate set
        without_defaults = False
        analyzer = cqasm.Analyzer("3.0", without_defaults)
        return analyzer

    @staticmethod
    def _check_analysis_result(result):
        if isinstance(result, list):
            raise Exception("Parsing error: " + ", ".join(result))

    def circuit_from_string(self, s: str):
        # Analysis result will be either an Abstract Syntax Tree (AST) or a list of error messages
        analyzer = self._create_analyzer()
        analysis_result = analyzer.analyze_string(s)
        Parser._check_analysis_result(analysis_result)
        ast = analysis_result

        # Create RegisterManager
        register_manager = RegisterManager.from_ast(ast)

        # Parse statements
        squirrel_ir = SquirrelIR()
        for statement in ast.block.statements:
            statement_name = self._parse_ast_string(statement.name)
            if "measure" in statement_name:
                generator_f = self.get_measurement_f(statement_name)
            else:
                generator_f = self.get_gate_f(statement_name)
            expanded_args = Parser._get_expanded_statement_args(statement.operands, register_manager)
            for arg_set in expanded_args:
                squirrel_ir.add_gate(generator_f(*arg_set))

        return Circuit(register_manager, squirrel_ir)
