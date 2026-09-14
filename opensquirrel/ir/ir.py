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
    def visit_str(self, s: String) -> Any: ...

    def visit_int(self, i: Int) -> Any: ...

    def visit_float(self, f: Float) -> Any: ...

    def visit_bit(self, bit: Bit) -> Any: ...

    def visit_qubit(self, qubit: Qubit) -> Any: ...

    def visit_axis(self, axis: Axis) -> Any: ...

    def visit_canonical_axis(self, axis: CanonicalAxis) -> Any: ...

    def visit_statement(self, statement: Statement) -> Any: ...

    def visit_asm_declaration(self, asm_declaration: AsmDeclaration) -> Any: ...

    def visit_instruction(self, instruction: Instruction) -> Any: ...

    def visit_unitary(self, unitary: Unitary) -> Any: ...

    def visit_gate(self, gate: Gate) -> Any: ...

    def visit_single_qubit_gate(self, gate: SingleQubitGate) -> Any: ...

    def visit_two_qubit_gate(self, gate: TwoQubitGate) -> Any: ...

    def visit_bloch_sphere_rotation(self, bloch_sphere_rotation: BlochSphereRotation) -> Any: ...

    def visit_bsr_no_params(self, gate: BsrNoParams) -> Any: ...

    def visit_bsr_full_params(self, gate: BsrFullParams) -> Any: ...

    def visit_bsr_angle_param(self, gate: BsrAngleParam) -> Any: ...

    def visit_bsr_unitary_params(self, gate: BsrUnitaryParams) -> Any: ...

    def visit_non_unitary(self, non_unitary: NonUnitary) -> Any: ...

    def visit_control_instruction(self, control_instruction: ControlInstruction) -> Any: ...

    def visit_measure(self, measure: Measure) -> Any: ...

    def visit_init(self, init: Init) -> Any: ...

    def visit_reset(self, reset: Reset) -> Any: ...

    def visit_barrier(self, barrier: Barrier) -> Any: ...

    def visit_wait(self, wait: Wait) -> Any: ...

    def visit_canonical_gate_semantic(self, canonical: CanonicalGateSemantic) -> Any: ...

    def visit_controlled_gate_semantic(self, controlled: ControlledGateSemantic) -> Any: ...

    def visit_matrix_gate_semantic(self, matrix: MatrixGateSemantic) -> Any: ...


class IRNode(ABC):
    @abstractmethod
    def accept(self, visitor: IRVisitor) -> Any: ...


class IR:
    def __init__(self) -> None:
        self.statements: list[Statement] = []

    def accept(self, visitor: IRVisitor) -> None:
        """Accepts visitor and processes the IR nodes."""
        for statement in self.statements:
            statement.accept(visitor)

    def add_asm_declaration(self, asm_declaration: AsmDeclaration) -> None:
        """Adds an assembly declaration to the IR.

        Args:
            asm_declaration (AsmDeclaration): The assembly declaration to add.

        """
        self.statements.append(asm_declaration)

    def add_gate(self, gate: Gate) -> None:
        """Adds a gate to the IR.

        Args:
            gate (Gate): The gate to add.

        """
        self.statements.append(gate)

    def add_non_unitary(self, non_unitary: NonUnitary) -> None:
        """Adds a non-unitary operation to the IR.

        Args:
            non_unitary (NonUnitary): The non-unitary operation to add.

        """
        self.statements.append(non_unitary)

    def add_statement(self, statement: Statement) -> None:
        """Adds a generic statement to the IR.

        Args:
            statement (Statement): The statement to add.

        """
        self.statements.append(statement)

    def reverse(self) -> IR:
        """Reverses the order of statements in the IR."""
        ir = IR()
        for statement in self.statements[::-1]:
            ir.add_statement(statement)
        return ir

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, IR):
            return False
        return self.statements == other.statements

    def __repr__(self) -> str:
        return f"IR: {self.statements}"

    def clear(self) -> None:
        """Clears all statements from the IR."""
        self.statements.clear()
