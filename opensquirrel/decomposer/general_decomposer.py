from abc import ABC, abstractmethod
from typing import Callable, List

from opensquirrel.common import are_matrices_equivalent_up_to_global_phase
from opensquirrel.squirrel_ir import Gate, SquirrelIR


class Decomposer(ABC):
    @staticmethod
    @abstractmethod
    def decompose(gate: Gate) -> [Gate]:
        raise NotImplementedError()


def check_gate_replacement(gate: Gate, replacement_gates: List[Gate]):
    gate_qubit_indices = [q.index for q in gate.get_qubit_operands()]
    replacement_gates_qubit_indices = set()
    [replacement_gates_qubit_indices.update([q.index for q in g.get_qubit_operands()]) for g in replacement_gates]

    if set(gate_qubit_indices) != replacement_gates_qubit_indices:
        raise ValueError(f"Replacement for gate {gate.name} does not seem to operate on the right qubits")

    from opensquirrel.circuit_matrix_calculator import get_circuit_matrix
    from opensquirrel.reindexer import get_reindexed_circuit

    replaced_matrix = get_circuit_matrix(get_reindexed_circuit([gate], gate_qubit_indices))
    replacement_matrix = get_circuit_matrix(get_reindexed_circuit(replacement_gates, gate_qubit_indices))
    if not are_matrices_equivalent_up_to_global_phase(replaced_matrix, replacement_matrix):
        raise Exception(f"Replacement for gate {gate.name} does not preserve the quantum state")


def decompose(squirrel_ir: SquirrelIR, decomposer: Decomposer):
    """Applies `decomposer` to every gate in the circuit, replacing each gate by the output of `decomposer`.
    When `decomposer` decides to not decomposer a gate, it needs to return a list with the intact gate as single
    element.
    """
    statement_index = 0
    while statement_index < len(squirrel_ir.statements):
        statement = squirrel_ir.statements[statement_index]

        if not isinstance(statement, Gate):
            statement_index += 1
            continue

        gate = statement
        replacement_gates: List[Gate] = decomposer.decompose(statement)
        check_gate_replacement(gate, replacement_gates)

        squirrel_ir.statements[statement_index: statement_index + 1] = replacement_gates
        statement_index += len(replacement_gates)


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
    generic_replacer = _GenericReplacer(gate_generator, f)

    decompose(squirrel_ir, generic_replacer)
