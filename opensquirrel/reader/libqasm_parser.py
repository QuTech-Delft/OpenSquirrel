from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, cast

import cqasm.v3x as cqasm

from opensquirrel.circuit import Circuit
from opensquirrel.default_gate_modifiers import ControlGateModifier, InverseGateModifier, PowerGateModifier
from opensquirrel.default_instructions import default_gate_set, default_non_unitary_set
from opensquirrel.ir import (
    IR,
    AsmDeclaration,
    Bit,
    Float,
    Gate,
    Int,
    NonUnitary,
    Qubit,
    Statement,
)
from opensquirrel.register_manager import RegisterManager

if TYPE_CHECKING:
    from opensquirrel.ir.semantics import BlochSphereRotation


class LibQasmParser:
    def __init__(self) -> None:
        self.ir = IR()

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
        ast_type = LibQasmParser._type_of(ast_expression)
        return bool(ast_type == cqasm.types.Qubit or ast_type == cqasm.types.QubitArray)

    @staticmethod
    def _is_bit_type(ast_expression: Any) -> bool:
        ast_type = LibQasmParser._type_of(ast_expression)
        return bool(ast_type == cqasm.types.Bit or ast_type == cqasm.types.BitArray)

    @staticmethod
    def _is_gate_instruction(ast_node: Any) -> bool:
        return isinstance(ast_node, cqasm.semantic.GateInstruction)

    @staticmethod
    def _is_non_unitary_instruction(ast_node: Any) -> bool:
        return isinstance(ast_node, cqasm.semantic.NonGateInstruction)

    @staticmethod
    def _is_asm_declaration(ast_node: Any) -> bool:
        return isinstance(ast_node, cqasm.semantic.AsmDeclaration)

    def _get_qubits(self, ast_qubit_expression: cqasm.values.VariableRef | cqasm.values.IndexRef) -> list[Qubit]:
        ret = []
        variable_name = ast_qubit_expression.variable.name
        if isinstance(ast_qubit_expression, cqasm.values.VariableRef):
            qubit_range = self.register_manager.get_qubit_range(variable_name)
            ret = [Qubit(index) for index in range(qubit_range.first, qubit_range.first + qubit_range.size)]
        if isinstance(ast_qubit_expression, cqasm.values.IndexRef):
            int_indices = [int(i.value) for i in ast_qubit_expression.indices]
            indices = [self.register_manager.get_qubit_index(variable_name, i) for i in int_indices]
            ret = [Qubit(index) for index in indices]
        return ret

    def _get_bits(self, ast_bit_expression: cqasm.values.VariableRef | cqasm.values.IndexRef) -> list[Bit]:
        ret = []
        variable_name = ast_bit_expression.variable.name
        if isinstance(ast_bit_expression, cqasm.values.VariableRef):
            bit_range = self.register_manager.get_bit_range(variable_name)
            ret = [Bit(index) for index in range(bit_range.first, bit_range.first + bit_range.size)]
        if isinstance(ast_bit_expression, cqasm.values.IndexRef):
            int_indices = [int(i.value) for i in ast_bit_expression.indices]
            indices = [self.register_manager.get_bit_index(variable_name, i) for i in int_indices]
            ret = [Bit(index) for index in indices]
        return ret

    def _get_instruction_operands(self, instruction: cqasm.semantic.Instruction) -> list[list[Any]]:
        """Get the list of lists of operands of an instruction.
        Notice that an instruction just has a list of operands. The outer list is needed to support SGMQ.
        For example, for CNOT q[0, 1] q[2, 3], this function returns [[Qubit(0), Qubit(1)], [Qubit(2), Qubit(3)]].
        """
        ret: list[list[Any]] = []
        for operand in instruction.operands:
            if self._is_qubit_type(operand):
                ret.append(self._get_qubits(operand))
            else:
                msg = "argument is not of qubit type"
                raise TypeError(msg)
        return ret

    @classmethod
    def _get_named_gate_parameters(cls, gate: cqasm.semantic.Gate) -> Any:
        """Get the parameters of a named gate.
        Notice the input gate can be a composition of gate modifiers acting on a named gate.
        """
        if gate.name in ["inv", "pow", "ctrl"]:
            return cls._get_named_gate_parameters(gate.gate)
        return [cls._ast_literal_to_ir_literal(parameter) for parameter in gate.parameters]

    def _get_expanded_instruction_args(self, instruction: cqasm.semantic.Instruction) -> list[tuple[Any, ...]]:
        """Construct a list with a list of qubits and a list of parameters, then return a zip of both lists.
        For example, for CRk(2) q[0, 1] q[2, 3], this function:
        1. constructs the list with a list of qubits [[Qubit(0), Qubit(1)], [Qubit(2), Qubit(3)]],
        2. appends the list of parameters [[Int(2)], [Int(2)]],
        3. zips the whole list and returns [(Qubit(0), Qubit(2), Int(2)), (Qubit(1), Qubit(3), Int(2))]
        """
        extended_operands = self._get_instruction_operands(instruction)
        if isinstance(instruction, cqasm.semantic.GateInstruction):
            gate_parameters = self._get_named_gate_parameters(instruction.gate)
        else:
            gate_parameters = [self._ast_literal_to_ir_literal(parameter) for parameter in instruction.parameters]
        if gate_parameters:
            number_of_operands = len(extended_operands[0])
            extended_gate_parameters = [gate_parameters] * number_of_operands
            return [
                (*operands, *parameters)
                for operands, parameters in zip(zip(*extended_operands), extended_gate_parameters)
            ]
        return list(zip(*extended_operands))

    def _get_expanded_measure_args(self, ast_args: Any) -> list[tuple[Any, ...]]:
        """Construct a list with a list of bits and a list of qubits, then return a zip of both lists.
        For example: [(Qubit(0), Bit(0)), (Qubit(1), Bit(1))]
        """
        # Notice the list is walked in reverse mode
        # This is because the AST measure node has a bit first operand and a qubit second operand
        expanded_args: list[list[Any]] = []
        for ast_arg in reversed(ast_args):
            if self._is_qubit_type(ast_arg):
                expanded_args.append(self._get_qubits(ast_arg))
            elif self._is_bit_type(ast_arg):
                expanded_args.append(self._get_bits(ast_arg))
            else:
                msg = "argument is neither of qubit nor bit type"
                raise TypeError(msg)
        return list(zip(*expanded_args))

    @staticmethod
    def _create_analyzer() -> cqasm.Analyzer:
        without_defaults = False
        return cqasm.Analyzer("3.0", without_defaults)

    @staticmethod
    def _check_analysis_result(result: Any) -> None:
        if isinstance(result, list):
            raise OSError("parsing error: " + ", ".join(result))

    def _get_gate_generator(self, instruction: cqasm.semantic.GateInstruction) -> Callable[..., Gate]:
        gate_name = instruction.gate.name
        if gate_name in ["inv", "pow", "ctrl"]:
            modified_gate_generator = cast(
                "Callable[..., BlochSphereRotation]", self._get_gate_generator(instruction.gate)
            )
            if gate_name == "inv":
                return InverseGateModifier(modified_gate_generator)
            if gate_name == "pow":
                gate = instruction.gate
                exponent = gate.parameters[0].value
                return PowerGateModifier(exponent, modified_gate_generator)
            if gate_name == "ctrl":
                return ControlGateModifier(modified_gate_generator)
            msg = "parsing error: unknown unitary instruction"

            raise OSError(msg)
        return lambda *args: default_gate_set[gate_name](*args)

    def _get_non_unitary_generator(self, instruction: cqasm.semantic.NonGateInstruction) -> Callable[..., NonUnitary]:
        return lambda *args: default_non_unitary_set[instruction.name](*args)

    def circuit_from_string(self, s: str) -> Circuit:
        # Analysis result will be either an Abstract Syntax Tree (AST) or a list of error messages
        analyzer = LibQasmParser._create_analyzer()
        analysis_result = analyzer.analyze_string(s)
        LibQasmParser._check_analysis_result(analysis_result)
        ast = analysis_result

        # Create RegisterManager
        self.register_manager = RegisterManager.from_ast(ast)

        # Parse statements
        expanded_args: list[tuple[Any, ...]] = []
        for statement in ast.block.statements:
            instruction_generator: Callable[..., Statement]
            if LibQasmParser._is_gate_instruction(statement):
                instruction_generator = self._get_gate_generator(statement)
                expanded_args = self._get_expanded_instruction_args(statement)
            elif LibQasmParser._is_non_unitary_instruction(statement):
                instruction_generator = self._get_non_unitary_generator(statement)
                expanded_args = (
                    self._get_expanded_measure_args(statement.operands)
                    if statement.name == "measure"
                    else self._get_expanded_instruction_args(statement)
                )
            elif LibQasmParser._is_asm_declaration(statement):
                asm_declaration = AsmDeclaration(statement.backend_name, statement.backend_code)
                self.ir.add_statement(asm_declaration)
            else:
                msg = "parsing error: unknown statement"
                raise OSError(msg)

            # For an SGMQ instruction:
            # expanded_args will contain a list with the list of qubits for each individual instruction,
            # while args will contain the list of qubits of an individual instruction
            if expanded_args:
                for args in expanded_args:
                    self.ir.add_statement(instruction_generator(*args))
                expanded_args = []

        return Circuit(self.register_manager, self.ir)
