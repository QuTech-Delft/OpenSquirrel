from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from typing import Any, overload

import cqasm.v3x as cqasm

from opensquirrel.circuit import Circuit
from opensquirrel.default_gates import default_gate_aliases, default_gate_set
from opensquirrel.default_measurements import default_measurement_set
from opensquirrel.instruction_library import GateLibrary, MeasurementLibrary
from opensquirrel.ir import IR, Bit, Float, Gate, Int, Measure, Qubit
from opensquirrel.register_manager import RegisterManager


class Parser(GateLibrary, MeasurementLibrary):
    def __init__(
        self,
        gate_set: Iterable[Callable[..., Gate]] = default_gate_set,
        gate_aliases: Mapping[str, Callable[..., Gate]] = default_gate_aliases,
        measurement_set: Iterable[Callable[..., Measure]] = default_measurement_set,
    ) -> None:
        GateLibrary.__init__(self, gate_set, gate_aliases)
        MeasurementLibrary.__init__(self, measurement_set)
        self.ir = None

    @staticmethod
    def _parse_ast_string(string: str) -> str:
        # FIXME: libqasm should return bytes, not the __repr__ of a bytes object ("b'q'")
        return string[2:-1]

    @staticmethod
    def _ast_literal_to_ir_literal(
        cqasm_literal_expression: cqasm.values.ConstInt | cqasm.values.ConstFloat,
    ) -> Int | Float | None:
        if type(cqasm_literal_expression) not in [cqasm.values.ConstInt, cqasm.values.ConstFloat]:
            raise TypeError(f"unrecognized type: {type(cqasm_literal_expression)}")
        if isinstance(cqasm_literal_expression, cqasm.values.ConstInt):
            return Int(cqasm_literal_expression.value)
        if isinstance(cqasm_literal_expression, cqasm.values.ConstFloat):
            return Float(cqasm_literal_expression.value)
        return None

    @staticmethod
    def _type_of(ast_expression: Any) -> type:
        if isinstance(ast_expression, cqasm.values.IndexRef) or isinstance(ast_expression, cqasm.values.VariableRef):
            return type(ast_expression.variable.typ)
        else:
            return type(ast_expression)

    @staticmethod
    def _size_of(ast_expression: Any) -> int:
        if isinstance(ast_expression, cqasm.values.IndexRef):
            return len(ast_expression.indices)
        elif isinstance(ast_expression, cqasm.values.VariableRef):
            return int(ast_expression.variable.typ.size)
        else:
            return 1

    @staticmethod
    def _is_qubit_type(ast_expression: Any) -> bool:
        ast_type = Parser._type_of(ast_expression)
        return bool(ast_type == cqasm.types.Qubit or ast_type == cqasm.types.QubitArray)

    @staticmethod
    def _is_bit_type(ast_expression: Any) -> bool:
        ast_type = Parser._type_of(ast_expression)
        return bool(ast_type == cqasm.types.Bit or ast_type == cqasm.types.BitArray)

    @staticmethod
    def _get_qubits(
        ast_qubit_expression: cqasm.values.VariableRef | cqasm.values.IndexRef, register_manager: RegisterManager
    ) -> list[Qubit]:
        ret = []
        variable_name = Parser._parse_ast_string(ast_qubit_expression.variable.name)
        if isinstance(ast_qubit_expression, cqasm.values.VariableRef):
            qubit_range = register_manager.get_qubit_range(variable_name)
            ret = [Qubit(index) for index in range(qubit_range.first, qubit_range.first + qubit_range.size)]
        if isinstance(ast_qubit_expression, cqasm.values.IndexRef):
            int_indices = [int(i.value) for i in ast_qubit_expression.indices]
            indices = [register_manager.get_qubit_index(variable_name, i) for i in int_indices]
            ret = [Qubit(index) for index in indices]
        return ret

    @staticmethod
    def _get_bits(
        ast_bit_expression: cqasm.values.VariableRef | cqasm.values.IndexRef, register_manager: RegisterManager
    ) -> list[Bit]:
        ret = []
        variable_name = Parser._parse_ast_string(ast_bit_expression.variable.name)
        if isinstance(ast_bit_expression, cqasm.values.VariableRef):
            bit_range = register_manager.get_bit_range(variable_name)
            ret = [Bit(index) for index in range(bit_range.first, bit_range.first + bit_range.size)]
        if isinstance(ast_bit_expression, cqasm.values.IndexRef):
            int_indices = [int(i.value) for i in ast_bit_expression.indices]
            indices = [register_manager.get_bit_index(variable_name, i) for i in int_indices]
            ret = [Bit(index) for index in indices]
        return ret

    @classmethod
    def _get_expanded_measure_args(cls, ast_args: Any, register_manager: RegisterManager) -> zip[tuple[Any, ...]]:
        """Construct a list with a list of bits and a list of qubits, then return a zip of both lists.
        For example: [(Qubit(0), Bit(0)), (Qubit(1), Bit(1))]

        Notice the  list is walked in reverse mode.
        This is because the AST measure node has a bit first operand and a qubit second operand.
        """
        expanded_args: list[list[Any]] = []
        for ast_arg in reversed(ast_args):
            if Parser._is_qubit_type(ast_arg):
                expanded_args.append(cls._get_qubits(ast_arg, register_manager))
            elif Parser._is_bit_type(ast_arg):
                expanded_args.append(cls._get_bits(ast_arg, register_manager))
            else:
                raise TypeError("received argument is not a (qu)bit")
        return zip(*expanded_args)

    @classmethod
    def _get_expanded_gate_args(cls, ast_args: Any, register_manager: RegisterManager) -> zip[tuple[Any, ...]]:
        """Construct a list with a list of qubits and a list of parameters, then return a zip of both lists.
        For example: [(Qubit(0), Float(pi)), (Qubit(1), Float(pi))]
        """
        number_of_operands = 0
        for ast_arg in ast_args:
            if Parser._is_qubit_type(ast_arg):
                number_of_operands += Parser._size_of(ast_arg)
        expanded_args: list[list[Any]] = []
        for ast_arg in ast_args:
            if Parser._is_qubit_type(ast_arg):
                expanded_args.append(cls._get_qubits(ast_arg, register_manager))
            else:
                expanded_args.append([cls._ast_literal_to_ir_literal(ast_arg)] * number_of_operands)
        return zip(*expanded_args)

    @overload
    @staticmethod
    def _get_cqasm_param_type_letters(squirrel_type: type[Qubit]) -> tuple[str, str]: ...

    @overload
    @staticmethod
    def _get_cqasm_param_type_letters(squirrel_type: type[Bit]) -> tuple[str, str]: ...

    @overload
    @staticmethod
    def _get_cqasm_param_type_letters(squirrel_type: type[Float] | type[Int]) -> str: ...

    @staticmethod
    def _get_cqasm_param_type_letters(
        squirrel_type: type[Qubit] | type[Bit] | type[Float] | type[Int],
    ) -> str | tuple[str, str]:
        if squirrel_type == Qubit:
            return "Q", "V"  # "V" is to allow array notations like q[3, 5, 7] and q[3:6]
        if squirrel_type == Bit:
            return "B", "W"  # "W" is to allow array notations like b[3, 5, 7] and b[3:6]
        if squirrel_type == Float:
            return "f"
        if squirrel_type == Int:
            return "i"

        raise TypeError("unsupported type")

    def _create_analyzer(self) -> cqasm.Analyzer:
        # TODO: we are temporarily using the default analyzer,
        #   mainly because there is a misalignment between the AST and the IR measure nodes.
        #   The AST currently produces measure nodes with a bit argument,
        #   but the IR doesn't consider yet that bit argument.
        #   In the future, we may want to go back to no using the default analyzer again,
        #   so that all gates are registered based on OpenSquirrel's default gate set
        without_defaults = False
        analyzer = cqasm.Analyzer("3.0", without_defaults)
        return analyzer

    @staticmethod
    def _check_analysis_result(result: Any) -> None:
        if isinstance(result, list):
            raise IOError("parsing error: " + ", ".join(result))

    def circuit_from_string(self, s: str) -> Circuit:
        # Analysis result will be either an Abstract Syntax Tree (AST) or a list of error messages
        analyzer = self._create_analyzer()
        analysis_result = analyzer.analyze_string(s)
        Parser._check_analysis_result(analysis_result)
        ast = analysis_result

        # Create RegisterManager
        register_manager = RegisterManager.from_ast(ast)

        # Parse statements
        ir = IR()
        for statement in ast.block.statements:
            statement_name = self._parse_ast_string(statement.name)
            if "measure" in statement_name:
                generator_f_measure = self.get_measurement_f(statement_name)
                expanded_args = Parser._get_expanded_measure_args(statement.operands, register_manager)
                for arg_set in expanded_args:
                    ir.add_measurement(generator_f_measure(*arg_set))
            else:
                generator_f_gate = self.get_gate_f(statement_name)
                expanded_args = Parser._get_expanded_gate_args(statement.operands, register_manager)
                for arg_set in expanded_args:
                    ir.add_gate(generator_f_gate(*arg_set))

        return Circuit(register_manager, ir)
