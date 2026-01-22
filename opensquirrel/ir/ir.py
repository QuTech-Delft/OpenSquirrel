from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from opensquirrel.ir import (
        AsmDeclaration,
        Axis,
        Barrier,
        Bit,
        Float,
        Gate,
        Init,
        Int,
        Measure,
        Qubit,
        Reset,
        String,
        Unitary,
        Wait,
    )
    from opensquirrel.ir.control_instruction import ControlInstruction
    from opensquirrel.ir.non_unitary import NonUnitary
    from opensquirrel.ir.semantics import (
        BlochSphereRotation,
        BsrAngleParam,
        BsrFullParams,
        BsrNoParams,
        BsrUnitaryParams,
        CanonicalGateSemantic,
        ControlledGateSemantic,
        MatrixGateSemantic,
    )
    from opensquirrel.ir.semantics.canonical_gate import CanonicalAxis
    from opensquirrel.ir.single_qubit_gate import SingleQubitGate
    from opensquirrel.ir.statement import Instruction, Statement
    from opensquirrel.ir.two_qubit_gate import TwoQubitGate


class IRVisitor:
    def visit_str(self, s: String) -> Any:
        pass

    def visit_int(self, i: Int) -> Any:
        pass

    def visit_float(self, f: Float) -> Any:
        pass

    def visit_bit(self, bit: Bit) -> Any:
        pass

    def visit_qubit(self, qubit: Qubit) -> Any:
        pass

    def visit_axis(self, axis: Axis) -> Any:
        pass

    def visit_canonical_axis(self, axis: CanonicalAxis) -> Any:
        pass

    def visit_statement(self, statement: Statement) -> Any:
        pass

    def visit_asm_declaration(self, asm_declaration: AsmDeclaration) -> Any:
        pass

    def visit_instruction(self, instruction: Instruction) -> Any:
        pass

    def visit_unitary(self, unitary: Unitary) -> Any:
        pass

    def visit_gate(self, gate: Gate) -> Any:
        pass

    def visit_single_qubit_gate(self, gate: SingleQubitGate) -> Any:
        pass

    def visit_two_qubit_gate(self, gate: TwoQubitGate) -> Any:
        pass

    def visit_bloch_sphere_rotation(self, bloch_sphere_rotation: BlochSphereRotation) -> Any:
        pass

    def visit_bsr_no_params(self, gate: BsrNoParams) -> Any:
        pass

    def visit_bsr_full_params(self, gate: BsrFullParams) -> Any:
        pass

    def visit_bsr_angle_param(self, gate: BsrAngleParam) -> Any:
        pass

    def visit_bsr_unitary_params(self, gate: BsrUnitaryParams) -> Any:
        pass

    def visit_non_unitary(self, non_unitary: NonUnitary) -> Any:
        pass

    def visit_control_instruction(self, control_instruction: ControlInstruction) -> Any:
        pass

    def visit_measure(self, measure: Measure) -> Any:
        pass

    def visit_init(self, init: Init) -> Any:
        pass

    def visit_reset(self, reset: Reset) -> Any:
        pass

    def visit_barrier(self, barrier: Barrier) -> Any:
        pass

    def visit_wait(self, wait: Wait) -> Any:
        pass

    def visit_canonical_gate_semantic(self, canonical: CanonicalGateSemantic) -> Any:
        pass

    def visit_controlled_gate_semantic(self, controlled: ControlledGateSemantic) -> Any:
        pass

    def visit_matrix_gate_semantic(self, matrix: MatrixGateSemantic) -> Any:
        pass


class IRNode(ABC):
    @abstractmethod
    def accept(self, visitor: IRVisitor) -> Any:
        pass


class IR:
    def __init__(self) -> None:
        self.statements: list[Statement] = []

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, IR):
            return False
        return self.statements == other.statements

    def __repr__(self) -> str:
        return f"IR: {self.statements}"

    def add_asm_declaration(self, asm_declaration: AsmDeclaration) -> None:
        self.statements.append(asm_declaration)

    def add_gate(self, gate: Gate) -> None:
        self.statements.append(gate)

    def add_non_unitary(self, non_unitary: NonUnitary) -> None:
        self.statements.append(non_unitary)

    def add_statement(self, statement: Statement) -> None:
        self.statements.append(statement)

    def reverse(self) -> IR:
        ir = IR()
        for statement in self.statements[::-1]:
            ir.add_statement(statement)
        return ir

    def accept(self, visitor: IRVisitor) -> None:
        for statement in self.statements:
            statement.accept(visitor)
