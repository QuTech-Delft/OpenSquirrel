from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from typing import Any

import cqasm.v3x as cqasm

from opensquirrel.circuit import Circuit
from opensquirrel.default_gates import default_gate_aliases, default_gate_set
from opensquirrel.default_measures import default_measure_set
from opensquirrel.default_resets import default_reset_set
from opensquirrel.instruction_library import GateLibrary, MeasureLibrary, ResetLibrary
from opensquirrel.ir import IR, Bit, Float, Gate, Int, Measure, Qubit, Reset
from opensquirrel.register_manager import RegisterManager


class Parser(GateLibrary, MeasureLibrary, ResetLibrary):
    def __init__(
        self,
        gate_set: Iterable[Callable[..., Gate]] = default_gate_set,
        gate_aliases: Mapping[str, Callable[..., Gate]] = default_gate_aliases,
        measure_set: Iterable[Callable[..., Measure]] = default_measure_set,
        reset_set: Iterable[Callable[..., Reset]] = default_reset_set,
    ) -> None:
        GateLibrary.__init__(self, gate_set, gate_aliases)
        MeasureLibrary.__init__(self, measure_set)
        ResetLibrary.__init__(self, reset_set)
        self.ir = None

    @staticmethod
    def _ast_literal_to_ir_literal(
        cqasm_literal_expression: cqasm.values.ConstInt | cqasm.values.ConstFloat,
    ) -> Int | Float | None:
        if type(cqasm_literal_expression) not in [
            cqasm.values.ConstInt,
            cqasm.values.ConstFloat,
        ]:
            msg = f"unrecognized type: {type(cqasm_literal_expression)}"
            raise TypeError(msg)
        if isinstance(cqasm_literal_expression, cqasm.values.ConstInt):
            return Int(cqasm_literal_expression.value)
        if isinstance(cqasm_literal_expression, cqasm.values.ConstFloat):
            return Float(cqasm_literal_expression.value)
        return None

    @staticmethod
    def _type_of(ast_expression: Any) -> type:
        if isinstance(ast_expression, (cqasm.values.IndexRef, cqasm.values.VariableRef)):
            return type(ast_expression.variable.typ)
        return type(ast_expression)

    @staticmethod
    def _size_of(ast_expression: Any) -> int:
        if isinstance(ast_expression, cqasm.values.IndexRef):
            return len(ast_expression.indices)
        if isinstance(ast_expression, cqasm.values.VariableRef):
            return int(ast_expression.variable.typ.size)
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
        ast_qubit_expression: cqasm.values.VariableRef | cqasm.values.IndexRef,
        register_manager: RegisterManager,
    ) -> list[Qubit]:
        ret = []
        variable_name = ast_qubit_expression.variable.name
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
        ast_bit_expression: cqasm.values.VariableRef | cqasm.values.IndexRef,
        register_manager: RegisterManager,
    ) -> list[Bit]:
        ret = []
        variable_name = ast_bit_expression.variable.name
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
                msg = "received argument is not a (qu)bit"
                raise TypeError(msg)
        return zip(*expanded_args)

    @classmethod
    def _get_expanded_reset_args(cls, ast_args: Any, register_manager: RegisterManager) -> zip[tuple[Any, ...]]:
        """Construct a list of qubits and return a zip.
        For example: [Qubit(0), Qubit(1), Qubit(2)]
        """
        expanded_args: list[Any] = []
        if len(ast_args) < 1:
            expanded_args += [Qubit(qubit_index) for qubit_index in range(register_manager.get_qubit_register_size())]
            return zip(expanded_args)
        for ast_arg in ast_args:
            if Parser._is_qubit_type(ast_arg):
                expanded_args += cls._get_qubits(ast_arg, register_manager)
            else:
                msg = "received argument is not a (qu)bit"
                raise TypeError(msg)
        return zip(expanded_args)

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

    @staticmethod
    def _create_analyzer() -> cqasm.Analyzer:
        without_defaults = False
        return cqasm.Analyzer("3.0", without_defaults)

    @staticmethod
    def _check_analysis_result(result: Any) -> None:
        if isinstance(result, list):
            raise OSError("parsing error: " + ", ".join(result))

    def circuit_from_string(self, s: str) -> Circuit:
        # Analysis result will be either an Abstract Syntax Tree (AST) or a
        # list of error messages
        analyzer = Parser._create_analyzer()
        analysis_result = analyzer.analyze_string(s)
        Parser._check_analysis_result(analysis_result)
        ast = analysis_result

        # Create RegisterManager
        register_manager = RegisterManager.from_ast(ast)

        # Parse statements
        ir = IR()
        for statement in ast.block.statements:
            if "measure" in statement.name:
                generator_f_measure = self.get_measure_f(statement.name)
                expanded_args = Parser._get_expanded_measure_args(statement.operands, register_manager)
                for arg_set in expanded_args:
                    ir.add_measure(generator_f_measure(*arg_set))
            elif "reset" in statement.name:
                generator_f_reset = self.get_reset_f(statement.name)
                expanded_args = Parser._get_expanded_reset_args(statement.operands, register_manager)
                for arg_set in expanded_args:
                    ir.add_reset(generator_f_reset(*arg_set))
            else:
                generator_f_gate = self.get_gate_f(statement.name)
                expanded_args = Parser._get_expanded_gate_args(statement.operands, register_manager)
                for arg_set in expanded_args:
                    ir.add_gate(generator_f_gate(*arg_set))

        return Circuit(register_manager, ir)
