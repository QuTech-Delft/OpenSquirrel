from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING

import numpy as np

from opensquirrel.circuit_matrix_calculator import get_circuit_matrix
from opensquirrel.common import (
    ATOL,
    are_matrices_equivalent_up_to_global_phase,
    calculate_phase_difference,
    get_phase_angle,
    is_identity_matrix_up_to_a_global_phase,
)
from opensquirrel.default_instructions import is_anonymous_gate
from opensquirrel.ir import Float, Gate, Rz
from opensquirrel.reindexer import get_reindexed_circuit

if TYPE_CHECKING:
    from opensquirrel.circuit import Circuit


class Decomposer(ABC):
    @abstractmethod
    def decompose(self, gate: Gate) -> list[Gate]:
        raise NotImplementedError()


def check_gate_replacement(gate: Gate, replacement_gates: Iterable[Gate], circuit: Circuit | None = None) -> list[Gate]:
    """
    Verifies the replacement gates against the given gate.
    Args:
        gate: original gate
        replacement_gates: gates replacing the gate
        circuit: circuit to verify
    Returns:
        Returns verified list of replacement gates with possible correction.
    """
    gate_qubit_indices = [q.index for q in gate.get_qubit_operands()]
    replacement_gates_qubit_indices = set()
    qubit_list = gate.get_qubit_operands()
    replaced_matrix = get_circuit_matrix(get_reindexed_circuit([gate], gate_qubit_indices))
    replacement_gates = list(replacement_gates)

    if is_identity_matrix_up_to_a_global_phase(replaced_matrix):
        return []

    for g in replacement_gates:
        replacement_gates_qubit_indices.update([q.index for q in g.get_qubit_operands()])

    if set(gate_qubit_indices) != replacement_gates_qubit_indices:
        msg = f"replacement for gate {gate.name} does not seem to operate on the right qubits"
        raise ValueError(msg)

    replacement_matrix = get_circuit_matrix(get_reindexed_circuit(replacement_gates, gate_qubit_indices))

    if not are_matrices_equivalent_up_to_global_phase(replaced_matrix, replacement_matrix):
        msg = f"replacement for gate {gate.name} does not preserve the quantum state"
        raise ValueError(msg)

    if circuit is not None:
        phase_difference = calculate_phase_difference(replaced_matrix, replacement_matrix)
        euler_phase = get_phase_angle(phase_difference)

        for q in gate.get_qubit_operands():
            circuit.phase_map.add_qubit_phase(q, euler_phase)

        if len(gate_qubit_indices) > 1:
            relative_phase = float(
                np.real(
                    circuit.phase_map.get_qubit_phase(qubit_list[1]) - circuit.phase_map.get_qubit_phase(qubit_list[0])
                )
            )
            if abs(relative_phase) > ATOL:
                replacement_gates.append(Rz(gate.get_qubit_operands()[0], Float(-1 * relative_phase)))

    return replacement_gates


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
        replacement_gates = check_gate_replacement(gate, replacement_gates, circuit)

        circuit.ir.statements[statement_index : statement_index + 1] = replacement_gates
        statement_index += len(replacement_gates)


class _GenericReplacer(Decomposer):
    def __init__(self, gate_type: type[Gate], replacement_gates_function: Callable[..., list[Gate]]) -> None:
        self.gate_type = gate_type
        self.replacement_gates_function = replacement_gates_function

    def decompose(self, gate: Gate) -> list[Gate]:
        if is_anonymous_gate(gate.name) or type(gate) is not self.gate_type:
            return [gate]
        return self.replacement_gates_function(*gate.arguments)


def replace(circuit: Circuit, gate: type[Gate], replacement_gates_function: Callable[..., list[Gate]]) -> None:
    """Does the same as decomposer, but only applies to a given gate."""
    generic_replacer = _GenericReplacer(gate, replacement_gates_function)

    decompose(circuit, generic_replacer)
