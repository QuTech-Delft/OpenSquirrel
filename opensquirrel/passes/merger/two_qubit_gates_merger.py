from __future__ import annotations

from typing import TYPE_CHECKING

import networkx as nx
import numpy as np

from opensquirrel.circuit_builder import CircuitBuilder
from opensquirrel.circuit_matrix_calculator import get_circuit_matrix
from opensquirrel.ir import IR, Gate, Instruction, Qubit
from opensquirrel.ir.semantics.matrix_gate import MatrixGateSemantic
from opensquirrel.ir.single_qubit_gate import SingleQubitGate
from opensquirrel.ir.two_qubit_gate import TwoQubitGate
from opensquirrel.passes.merger.general_merger import Merger

if TYPE_CHECKING:
    from opensquirrel.circuit import Circuit


def build_graph(ir: IR) -> nx.DiGraph:
    n = len(ir.statements)
    graph = nx.DiGraph()
    graph.add_nodes_from(
        (i, {"qubit_indices": statement.qubit_indices})
        for i, statement in enumerate(ir.statements)
        if isinstance(statement, Instruction)
    )

    for i, statement in enumerate(ir.statements):
        if not isinstance(statement, Instruction):
            continue

        qubit_indices = set(statement.qubit_indices)
        for j in range(i + 1, n):
            other_statement = ir.statements[j]
            if isinstance(other_statement, Instruction):
                other_qubit_indices = set(other_statement.qubit_indices)

                if inter := qubit_indices.intersection(other_qubit_indices):
                    graph.add_edge(i, j, qubit_index=tuple(inter))
                    qubit_indices = qubit_indices.difference(inter)

            if not qubit_indices:
                break

    if not nx.is_directed_acyclic_graph(graph):
        raise ValueError

    return graph


def group_gates(graph: nx.DiGraph) -> list[tuple[set[int], set[int]]]:
    groups: list[tuple[set, set]] = []
    available_nodes = set(graph.nodes)

    if len(available_nodes) == 1:
        return [(available_nodes, set(graph.nodes[0]["qubit_indices"]))]

    for edge in graph.edges():
        source_node = graph.nodes[edge[0]]
        target_node = graph.nodes[edge[1]]

        edge_nodes = {edge[0], edge[1]}
        active_nodes = edge_nodes & available_nodes
        qubit_indices = set(source_node["qubit_indices"]) | set(target_node["qubit_indices"])

        matched_group = False
        for group, indices in groups:
            if not (group & edge_nodes):
                continue

            if len(indices) == 1:
                indices.update(qubit_indices)

            if qubit_indices.issubset(indices):
                group.update(active_nodes)
                available_nodes.difference_update(active_nodes)

            matched_group = True
            break

        if not matched_group:
            groups.append((active_nodes, set(qubit_indices)))
            available_nodes.difference_update(active_nodes)

    # Sort the groups, such that the order of the two qubit gates is preserved.
    return sorted(groups, key=lambda x: _first_two_qubit_gate(graph, x[0]))


def _first_two_qubit_gate(graph: nx.DiGraph, group: set[int]) -> int:
    """Return the first statement index pointing to a two qubit gate."""
    return min(i for i in group if len(graph.nodes[i]["qubit_indices"]) == 2)


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


def _merge_gate_group(ir: IR, group: set[int], qubit_indices: set[int]) -> TwoQubitGate:
    builder = CircuitBuilder(len(qubit_indices))
    for index in group:
        statement = ir.statements[index]
        if isinstance(statement, Gate):
            statement = normalize_gate_indices(statement)
            builder.add_instruction(statement)

    sub_circuit_matrix = _get_sub_circuit_matrix(builder.to_circuit())
    return TwoQubitGate(*qubit_indices, gate_semantic=MatrixGateSemantic(sub_circuit_matrix))


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
        graph = build_graph(ir)
        if len(graph.nodes) == 1:
            return

        groups = group_gates(graph)
        ir.statements = [_merge_gate_group(ir, group, qubit_indices) for group, qubit_indices in groups]
