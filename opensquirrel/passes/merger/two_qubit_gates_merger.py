from copy import copy

import numpy as np

from opensquirrel.circuit import Circuit
from opensquirrel.circuit_builder import CircuitBuilder
from opensquirrel.circuit_matrix_calculator import get_circuit_matrix
from opensquirrel.ir import IR, Gate, Qubit
from opensquirrel.ir.semantics.matrix_gate import MatrixGateSemantic
from opensquirrel.ir.single_qubit_gate import SingleQubitGate
from opensquirrel.ir.two_qubit_gate import TwoQubitGate
from opensquirrel.passes.merger.general_merger import Merger


def group_gates(gates: list[list[int]]) -> list[tuple[tuple[int, int], list[int]]]:
    groups = []
    group = set()
    statement_indices = []
    for i, qubit_indices in enumerate(gates):
        # Reset group if current statement is not a Gate
        if not qubit_indices:
            if group:
                groups.append((tuple(group), copy(statement_indices)))
            group.clear()
            statement_indices.clear()
            continue

        # If the group has more than 2 qubits, it means that we have encountered a new group of gates.
        if len(group | set(qubit_indices)) > 2:
            if group:
                groups.append((tuple(group), copy(statement_indices)))
            group = set(qubit_indices)
            statement_indices.clear()

        group.update(qubit_indices)
        statement_indices.append(i)

    if group:
        groups.append((tuple(group), copy(statement_indices)))
    return groups


def normalize_gate_indices(gate: Gate) -> Gate:
    if isinstance(gate, TwoQubitGate):
        gate.qubit0 = Qubit(gate.qubit0.index % 2)
        gate.qubit1 = Qubit(gate.qubit1.index % 2)
        return gate

    if isinstance(gate, SingleQubitGate):
        gate.qubit = Qubit(gate.qubit.index % 2)
        return gate

    msg = f"Unsupported gate type: {type(gate)}"
    raise TypeError(msg)

def _get_sub_circuit_matrix(circuit: Circuit) -> np.ndarray:
    # `get_circuit_matrix` uses the convention of the first qubit being the most significant bit,
    # so we need to swap the qubits before and after calculating the matrix
    swap = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]])
    return swap @ get_circuit_matrix(circuit) @ swap

class TwoQubitGatesMerger(Merger):
    def merge(self, ir: IR, qubit_register_size: int) -> None:
        """Merge all consecutive two-qubit gates in the circuit.

        Args:
            ir (IR): Intermediate representation of the circuit.
            qubit_register_size (int): Size of the qubit register

        """

        gates = [statement.qubit_indices if isinstance(statement, Gate) else [] for statement in ir.statements]
        groups = group_gates(gates)

        new_gates = []

        for qubit_indices, statement_indices in groups:
            if len(statement_indices) == 1:
                new_gates.append(ir.statements[statement_indices[0]])
                continue

            builder = CircuitBuilder(len(qubit_indices))
            for statement_index in statement_indices:
                statement = ir.statements[statement_index]
                if isinstance(statement, Gate):
                    statement = normalize_gate_indices(statement)
                    builder.add_instruction(statement)

            sub_circuit_matrix = _get_sub_circuit_matrix(builder.to_circuit())
            gate = TwoQubitGate(*qubit_indices, gate_semantic=MatrixGateSemantic(sub_circuit_matrix))
            new_gates.append(gate)

        # Replace the original statements with the merged gates
        new_statements = []
        current_index = 0
        for new_gate, (_, statement_indices) in zip(new_gates, groups, strict=True):
            if current_index < statement_indices[0]:
                new_statements.extend(ir.statements[current_index : statement_indices[0]])

            new_statements.append(new_gate)
            current_index = statement_indices[-1] + 1

        # Replace the original statements with the merged gates
        ir.statements = new_statements

