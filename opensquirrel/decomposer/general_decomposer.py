from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable

from opensquirrel.circuit_matrix_calculator import get_circuit_matrix
from opensquirrel.common import (
    are_matrices_equivalent_up_to_global_phase,
    calculate_phase_difference,
    to_euler_form,
    ATOL
)
from opensquirrel.ir import IR, Gate
from opensquirrel.default_gates import Rz
from opensquirrel.reindexer import get_reindexed_circuit
from opensquirrel.circuit import Circuit

class Decomposer(ABC):
    @abstractmethod
    def decompose(self, gate: Gate) -> list[Gate]:
        raise NotImplementedError()


def check_gate_replacement(gate: Gate, replacement_gates: Iterable[Gate], qc: Circuit | None = None) -> list[Gate]:
    """
    Verifies the replacement gates against the given gate.
    Args:
        gate: original gate
        replacement_gates: gates replacing the gate

    Returns:
        Returns verified list of replacement gates with possible correction.
    """
    gate_qubit_indices = [q.index for q in gate.get_qubit_operands()]
    qubit_list = gate.get_qubit_operands()
    replacement_gates_qubit_indices = set()
    for g in replacement_gates:
        replacement_gates_qubit_indices.update([q.index for q in g.get_qubit_operands()])

    if set(gate_qubit_indices) != replacement_gates_qubit_indices:
        msg = f"replacement for gate {gate.name} does not seem to operate on the right qubits"
        raise ValueError(msg)

    replaced_matrix = get_circuit_matrix(get_reindexed_circuit([gate], gate_qubit_indices))
    replacement_matrix = get_circuit_matrix(get_reindexed_circuit(replacement_gates, gate_qubit_indices))

    if not are_matrices_equivalent_up_to_global_phase(replaced_matrix, replacement_matrix):
        msg = f"replacement for gate {gate.name} does not preserve the quantum state"
        raise ValueError(msg)

    if qc is not None:
        for qubit in gate.get_qubit_operands():
            print("Get phase: " + str(qc.get_qubit_phase(qubit)) + " " + str(qubit))

        phase_difference = calculate_phase_difference(replaced_matrix, replacement_matrix)
        euler_phase = to_euler_form(phase_difference)
        print("Add phase: " + str(euler_phase) + " " + str(qubit_list))
        [qc.add_qubit_phase(q, euler_phase) for q in gate.get_qubit_operands()]
        #if euler_phase > ATOL:
        #    print([q.get_phase() for q in gate.get_qubit_operands()])
        #    print([q for q in gate.get_qubit_operands()])

        if len(gate_qubit_indices) > 1:
            relative_phase = qc.get_qubit_phase(qubit_list[1]) - qc.get_qubit_phase(qubit_list[0])
            if abs(relative_phase) > ATOL:
                list(replacement_gates).append(Rz(gate.get_qubit_operands()[0], -1*relative_phase))

    return list(replacement_gates)


def decompose(circuit: Circuit, decomposer: Decomposer) -> None:
    """Applies `decomposer` to every gate in the circuit, replacing each gate by the output of `decomposer`.
    When `decomposer` decides to not decomposer a gate, it needs to return a list with the intact gate as single
    element.
    """
    statement_index = 0
    while statement_index < len(circuit.ir.statements):
        statement = circuit.ir.statements[statement_index]

        if not isinstance(statement, Gate):
            statement_index += 1
            continue

        gate = statement
        replacement_gates: list[Gate] = decomposer.decompose(statement)
        replacement_gates = check_gate_replacement(gate, replacement_gates)

        circuit.ir.statements[statement_index: statement_index + 1] = replacement_gates
        statement_index += len(replacement_gates)


class _GenericReplacer(Decomposer):
    def __init__(self, gate_generator: Callable[..., Gate], replacement_function: Callable[..., list[Gate]]) -> None:
        self.gate_generator = gate_generator
        self.replacement_function = replacement_function

    def decompose(self, g: Gate) -> list[Gate]:
        if g.is_anonymous or g.generator != self.gate_generator:
            return [g]
        arguments = () if g.arguments is None else g.arguments
        return self.replacement_function(*arguments)


def replace(circuit: Circuit, gate_generator: Callable[..., Gate], f: Callable[..., list[Gate]]) -> None:
    """Does the same as decomposer, but only applies to a given gate."""
    generic_replacer = _GenericReplacer(gate_generator, f)

    decompose(circuit, generic_replacer)
