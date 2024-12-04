from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

import cqasm.v3x as cqasm

from opensquirrel import instruction_library
from opensquirrel.circuit import Circuit
from opensquirrel.default_gate_modifiers import ControlGateModifier, InverseGateModifier, PowerGateModifier
from opensquirrel.ir import IR, Bit, BlochSphereRotation, Float, Gate, Int, NonUnitary, Qubit, Statement
from opensquirrel.register_manager import RegisterManager


class Parser:
    def __init__(self) -> None:
        self.ir = None

    @staticmethod
    def _ast_literal_to_ir_literal(
        ast_literal: cqasm.values.ConstInt | cqasm.values.ConstFloat | None,
    ) -> Int | Float | None:
        if type(ast_literal) not in [cqasm.values.ConstInt, cqasm.values.ConstFloat, type(None)]:
            msg = f"unrecognized type: {type(ast_literal)}"
            raise TypeError(msg)
        if isinstance(ast_literal, cqasm.values.ConstInt):
            return Int(ast_literal.value)
        if isinstance(ast_literal, cqasm.values.ConstFloat):
            return Float(ast_literal.value)
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
    def _is_non_unitary_instruction(ast_node: Any) -> bool:
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
    def _get_instruction_operands(
        cls,
        instruction: cqasm.semantic.Instruction,
        register_manager: RegisterManager,
    ) -> list[list[Any]]:
        """Get the list of lists of operands of an instruction.
        Notice that an instruction just has a list of operands. The outer list is needed to support SGMQ.
        For example, for CNOT q[0, 1] q[2, 3], this function returns [[Qubit(0), Qubit(1)], [Qubit(2), Qubit(3)]].
        """
        ret: list[list[Any]] = []
        for operand in instruction.operands:
            if cls._is_qubit_type(operand):
                ret.append(cls._get_qubits(operand, register_manager))
            else:
                msg = "argument is not of qubit type"
                raise TypeError(msg)
        return ret

    @classmethod
    def _get_named_gate_param(cls, gate: cqasm.semantic.Gate) -> Any:
        """Get the parameter of a named gate.
        Notice the input gate can be a composition of gate modifiers acting on a named gate.
        """
        if gate.name in ["inv", "pow", "ctrl"]:
            return cls._get_named_gate_param(gate.gate)
        return cls._ast_literal_to_ir_literal(gate.parameter)

    @classmethod
    def _get_expanded_instruction_args(
        cls,
        instruction: cqasm.semantic.Instruction,
        register_manager: RegisterManager,
    ) -> zip[tuple[Any, ...]]:
        """Construct a list with a list of qubits and a list of parameters, then return a zip of both lists.
        For example, for CRk(2) q[0, 1] q[2, 3], this function first constructs the list with a list of qubits
        [[Qubit(0), Qubit(1)], [Qubit(2), Qubit(3)]], then appends the list of parameters [Int(2), Int(2)],
        and finally zips the whole list and returns [(Qubit(0), Qubit(1), Int(2)), (Qubit(2), Qubit(3), Int(2))]
        """
        ret = cls._get_instruction_operands(instruction, register_manager)
        if isinstance(instruction, cqasm.semantic.GateInstruction):
            gate_parameter = cls._get_named_gate_param(instruction.gate)
        else:
            gate_parameter = cls._ast_literal_to_ir_literal(instruction.parameter)
        if gate_parameter:
            number_of_operands = len(ret[0])
            ret.append([gate_parameter] * number_of_operands)
        return zip(*ret)

    @classmethod
    def _get_expanded_measure_args(cls, ast_args: Any, register_manager: RegisterManager) -> zip[tuple[Any, ...]]:
        """Construct a list with a list of bits and a list of qubits, then return a zip of both lists.
        For example: [(Qubit(0), Bit(0)), (Qubit(1), Bit(1))]
        """
        # Notice the list is walked in reverse mode
        # This is because the AST measure node has a bit first operand and a qubit second operand
        expanded_args: list[list[Any]] = []
        for ast_arg in reversed(ast_args):
            if cls._is_qubit_type(ast_arg):
                expanded_args.append(cls._get_qubits(ast_arg, register_manager))
            elif cls._is_bit_type(ast_arg):
                expanded_args.append(cls._get_bits(ast_arg, register_manager))
            else:
                msg = "argument is neither of qubit nor bit type"
                raise TypeError(msg)
        return zip(*expanded_args)

    @staticmethod
    def _create_analyzer() -> cqasm.Analyzer:
        without_defaults = False
        return cqasm.Analyzer("3.0", without_defaults)

    @staticmethod
    def _check_analysis_result(result: Any) -> None:
        if isinstance(result, list):
            raise OSError("parsing error: " + ", ".join(result))

    @staticmethod
    def _get_gate_f(instruction: cqasm.semantic.GateInstruction) -> Callable[..., Gate]:
        gate_name = instruction.gate.name
        if gate_name in ["inv", "pow", "ctrl"]:
            modified_gate_f = cast(Callable[..., BlochSphereRotation], Parser._get_gate_f(instruction.gate))
            if gate_name == "inv":
                return InverseGateModifier(modified_gate_f)
            if gate_name == "pow":
                return PowerGateModifier(instruction.gate.parameter.value, modified_gate_f)
            if gate_name == "ctrl":
                return ControlGateModifier(modified_gate_f)
            msg = "parsing error: unknown unitary instruction"
            raise OSError(msg)
        return instruction_library.get_gate_f(gate_name)

    @staticmethod
    def _get_non_unitary_f(instruction: cqasm.semantic.NonGateInstruction) -> Callable[..., NonUnitary]:
        return instruction_library.get_non_unitary_f(instruction.name)

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
                expanded_args = Parser._get_expanded_instruction_args(statement, register_manager)
            elif Parser._is_non_unitary_instruction(statement):
                instruction_generator = self._get_non_unitary_f(statement)
                expanded_args = (
                    Parser._get_expanded_measure_args(statement.operands, register_manager)
                    if statement.name == "measure"
                    else Parser._get_expanded_instruction_args(statement, register_manager)
                )
            else:
                msg = "parsing error: unknown statement"
                raise OSError(msg)

            # For an SGMQ instruction:
            # expanded_args will contain a list with the list of qubits for each individual instruction,
            # while args will contain the list of qubits of an individual instruction
            for args in expanded_args:
                ir.add_statement(instruction_generator(*args))
        return Circuit(register_manager, ir)
