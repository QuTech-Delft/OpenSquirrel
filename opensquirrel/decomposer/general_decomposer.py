from abc import ABC, abstractmethod
from typing import Callable, List

from opensquirrel.common import are_matrices_equivalent_up_to_global_phase
from opensquirrel.squirrel_ir import (
    BlochSphereRotation,
    ControlledGate,
    Gate,
    MatrixGate,
    Qubit,
    SquirrelIR,
    SquirrelIRVisitor,
)


class Decomposer(ABC):
    @staticmethod
    @abstractmethod
    def decompose(gate: Gate) -> [Gate]:
        raise NotImplementedError()


class _QubitReIndexer(SquirrelIRVisitor):
    def __init__(self, mappings: List[Qubit]):
        self.mappings = mappings

    def visit_bloch_sphere_rotation(self, g: BlochSphereRotation):
        result = BlochSphereRotation(
            qubit=Qubit(self.mappings.index(g.qubit)), angle=g.angle, axis=g.axis, phase=g.phase
        )
        return result

    def visit_matrix_gate(self, g: MatrixGate):
        mapped_operands = [Qubit(self.mappings.index(op)) for op in g.operands]
        result = MatrixGate(matrix=g.matrix, operands=mapped_operands)
        return result

    def visit_controlled_gate(self, controlled_gate: ControlledGate):
        control_qubit = Qubit(self.mappings.index(controlled_gate.control_qubit))
        target_gate = controlled_gate.target_gate.accept(self)
        result = ControlledGate(control_qubit=control_qubit, target_gate=target_gate)
        return result


def check_valid_replacement(statement, replacement):
    expected_qubit_operands = statement.get_qubit_operands()
    replacement_qubit_operands = set()
    [replacement_qubit_operands.update(g.get_qubit_operands()) for g in replacement]

    if set(expected_qubit_operands) != replacement_qubit_operands:
        raise ValueError(f"Replacement for gate {statement.name} does not seem to operate on the right qubits")

    from opensquirrel.utils.matrix_expander import get_matrix_after_qubit_remapping

    replacement_matrix = get_matrix_after_qubit_remapping(replacement, expected_qubit_operands)
    replaced_matrix = get_matrix_after_qubit_remapping([statement], expected_qubit_operands)

    if not are_matrices_equivalent_up_to_global_phase(replacement_matrix, replaced_matrix):
        raise Exception(f"Replacement for gate {statement.name} does not preserve the quantum state")


def decompose(squirrel_ir: SquirrelIR, decomposer: Decomposer):
    """Applies `decomposer` to every gate in the circuit, replacing each gate by the output of `decomposer`.
    When `decomposer` decides to not decomposer a gate, it needs to return a list with the intact gate as single element.
    """
    statement_index = 0
    while statement_index < len(squirrel_ir.statements):
        statement = squirrel_ir.statements[statement_index]

        if not isinstance(statement, Gate):
            statement_index += 1
            continue

        replacement: List[Gate] = decomposer.decompose(statement)

        check_valid_replacement(statement, replacement)

        squirrel_ir.statements[statement_index: statement_index + 1] = replacement
        statement_index += len(replacement)


class _GenericReplacer(Decomposer):
    def __init__(self, gate_generator: Callable[..., Gate], replacement_function):
        self.gate_generator = gate_generator
        self.replacement_function = replacement_function

    def decompose(self, g: Gate) -> [Gate]:
        if g.is_anonymous or g.generator != self.gate_generator:
            return [g]
        return self.replacement_function(*g.arguments)


def replace(squirrel_ir: SquirrelIR, gate_generator: Callable[..., Gate], f):
    """Does the same as decomposer, but only applies to a given gate."""

    def generic_replacer(g: Gate) -> [Gate]:
        if g.is_anonymous or g.generator != gate_generator:
            return [g]
        return f(*g.arguments)

    generic_replacer = _GenericReplacer(gate_generator, f)

    decompose(squirrel_ir, generic_replacer)
