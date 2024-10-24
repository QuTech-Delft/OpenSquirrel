from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from types import NoneType
from typing import Any, cast

import cqasm.v3x as cqasm

from opensquirrel.circuit import Circuit
from opensquirrel.default_gates import default_gate_aliases, default_gate_set
from opensquirrel.default_gate_modifiers import ControlGateModifier, InverseGateModifier, PowerGateModifier
from opensquirrel.default_measures import default_measure_set
from opensquirrel.default_resets import default_reset_set
from opensquirrel.instruction_library import GateLibrary, MeasureLibrary, ResetLibrary
from opensquirrel.ir import IR, Bit, BlochSphereRotation, Float, Gate, Int, Measure, Qubit, Reset, Statement
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
        cqasm_literal_expression: cqasm.values.ConstInt | cqasm.values.ConstFloat | None,
    ) -> Int | Float | None:
        if type(cqasm_literal_expression) not in [cqasm.values.ConstInt, cqasm.values.ConstFloat, NoneType]:
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
    def _is_gate_instruction(ast_node: Any) -> bool:
        return isinstance(ast_node, cqasm.semantic.GateInstruction)

    @staticmethod
    def _is_non_gate_instruction(ast_node: Any) -> bool:
        return isinstance(ast_node, cqasm.semantic.NonGateInstruction)

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
    def _get_expanded_gate_args(cls, ast_args: Any, register_manager: RegisterManager) -> zip[tuple[Any, ...]]:
        """Construct a list with a list of qubit operands, then return a zip of all the inner lists.

        For example, for a CNOT q[0, 1], q[2, 3] instruction,
        it first constructs [[Qubit(0), Qubit(1)], [Qubit(2), Qubit(3)]],
        and then returns [(Qubit(0), Qubit(2)), (Qubit(1), Qubit(3))]

        Note that _get_expanded_gate_args is only needed for Single-Gate-Multiple-Qubit (SGMQ).
        """
        expanded_args: list[list[Qubit]] = []
        for ast_arg in ast_args:
            expanded_args.append(cls._get_qubits(ast_arg, register_manager))
        return zip(*expanded_args)

    @staticmethod
    def _create_analyzer() -> cqasm.Analyzer:
        without_defaults = False
        return cqasm.Analyzer("3.0", without_defaults)

    @staticmethod
    def _check_analysis_result(result: Any) -> None:
        if isinstance(result, list):
            raise OSError("parsing error: " + ", ".join(result))

    def _get_gate_f(self, instruction: cqasm.semantic.GateInstruction) -> Callable[..., Gate]:
        gate_name = instruction.gate.name
        if gate_name == "inv" or gate_name == "pow" or gate_name == "ctrl":
            modified_gate_f = cast(Callable[..., BlochSphereRotation], self._get_gate_f(instruction.gate))
            if gate_name == "inv":
                return InverseGateModifier(modified_gate_f)
            elif gate_name == "pow":
                return PowerGateModifier(instruction.gate.parameter.value, modified_gate_f)
            elif gate_name == "ctrl":
                return ControlGateModifier(modified_gate_f)
        else:
            gate_parameter = Parser._ast_literal_to_ir_literal(instruction.gate.parameter)
            return self.get_gate_f(gate_name, gate_parameter)

    def _get_non_gate_f(self, instruction: cqasm.semantic.NonGateInstruction) -> Callable[..., Statement]:
        if "measure" in instruction.name:
            return self.get_measure_f(instruction.name)
        elif "reset" in instruction.name:
            return self.get_reset_f(instruction.name)
        else:
            raise OSError("parsing error: unknown non-unitary instruction")

    def circuit_from_string(self, s: str) -> Circuit:
        # Analysis result will be either an Abstract Syntax Tree (AST) or a list of error messages
        analyzer = Parser._create_analyzer()
        analysis_result = analyzer.analyze_string(s)
        Parser._check_analysis_result(analysis_result)
        ast = analysis_result

        # Create RegisterManager
        register_manager = RegisterManager.from_ast(ast)

        # Parse statements
        ir = IR()
        for statement in ast.block.statements:
            instruction_generator: Callable[..., Statement]
            if Parser._is_gate_instruction(statement):
                instruction_generator = self._get_gate_f(statement)
            elif Parser._is_non_gate_instruction(statement):
                instruction_generator = self._get_non_gate_f(statement)
            else:
                raise OSError("parsing error: unknown statement")
            for args in Parser._get_expanded_gate_args(statement.operands, register_manager):
                ir.add_statement(instruction_generator(*args))

        return Circuit(register_manager, ir)
