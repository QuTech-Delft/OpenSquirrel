from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any, TypeVar

from opensquirrel.circuit_matrix_calculator import get_circuit_matrix
from opensquirrel.common import are_matrices_equivalent_up_to_global_phase, is_identity_matrix_up_to_a_global_phase
from opensquirrel.ir import IR, Gate, Instruction, Measure
from opensquirrel.reindexer import get_reindexed_circuit

InstructionType = TypeVar("InstructionType", bound=Instruction)


class Decomposer(ABC):
    def __init__(self, **kwargs: Any) -> None: ...

    @abstractmethod
    def decompose(self, instruction: InstructionType) -> list[InstructionType]: ...


def decompose(ir: IR, decomposer: Decomposer) -> None:
    """Decomposes the statements in the circuit IR using the provided decomposer.

    Args:
        ir (IR): The circuit IR to decompose.
        decomposer (Decomposer): The decomposer to use for decomposing the gates.

    """
    statement_index = 0
    while statement_index < len(ir.statements):
        statement = ir.statements[statement_index]

        if isinstance(statement, Gate):
            gate = statement
            replacement_gates: list[Gate] = decomposer.decompose(statement)
            check_gate_decomposition(gate, replacement_gates)

            ir.statements[statement_index : statement_index + 1] = replacement_gates
            statement_index += len(replacement_gates)

        elif isinstance(statement, Measure):
            measure_decomposition = decomposer.decompose(statement)
            ir.statements[statement_index : statement_index + 1] = measure_decomposition
            statement_index += len(measure_decomposition)
        else:
            statement_index += 1


def check_gate_decomposition(gate: Gate, decomposition_gates: Iterable[Gate]) -> None:
    """Checks that the decomposition gate(s) are valid by verifying that they operate on the same
    qubits and preserve the quantum state up to a global phase.

    Args:
        gate (Gate): Gate that is being decomposed.
        decomposition_gates (Iterable[Gate]): Gate(s) that are decomposing the original gate.

    Raises:
        ValueError: If the decomposition gates do not operate on the same qubits as the original gate.
        ValueError: If the decomposition gates do not preserve the quantum state up to a global phase.

    """
    gate_qubit_indices = gate.qubit_indices
    decomposition_gates_qubit_indices = set()
    decomposed_matrix = get_circuit_matrix(get_reindexed_circuit([gate], gate_qubit_indices))

    if is_identity_matrix_up_to_a_global_phase(decomposed_matrix):
        return

    for decomposition_gate in decomposition_gates:
        decomposition_gates_qubit_indices.update(decomposition_gate.qubit_indices)

    if set(gate_qubit_indices) != decomposition_gates_qubit_indices:
        msg = f"decomposition for gate {gate.name!r} does not operate on the correct qubits"
        raise ValueError(msg)

    decomposition_matrix = get_circuit_matrix(get_reindexed_circuit(decomposition_gates, gate_qubit_indices))

    if not are_matrices_equivalent_up_to_global_phase(decomposed_matrix, decomposition_matrix):
        msg = f"decomposition for gate {gate.name!r} does not preserve the quantum state"
        raise ValueError(msg)
