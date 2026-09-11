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


def _add_asm_declaration_edges(graph: nx.DiGraph, ir: IR) -> nx.DiGraph:
    n = len(ir.statements)
    last_non_instruction = 0
    for i, statement in enumerate(ir.statements):
        if isinstance(statement, Instruction):
            continue

        for j in range(n):
            if not isinstance(ir.statements[j], Instruction) and i != j and i > last_non_instruction:
                last_non_instruction = j
                break

            qubit_indices = graph.nodes[j]["qubit_indices"]
            if not qubit_indices:
                continue

            if j < i and graph.out_degree(j) == len(qubit_indices) - 1:
                graph.add_edge(j, i)

            if j > i and graph.in_degree(j) == len(qubit_indices) - 1:
                graph.add_edge(i, j)
    return graph


def build_graph(ir: IR) -> nx.DiGraph:
    n = len(ir.statements)
    graph = nx.DiGraph()
    graph.add_nodes_from(
        (i, {"qubit_indices": statement.qubit_indices if isinstance(statement, Instruction) else None})
        for i, statement in enumerate(ir.statements)
    )

    for i, statement in enumerate(ir.statements):
        if not isinstance(statement, Instruction):
            continue

        qubit_indices = set(statement.qubit_indices)
        for j in range(i + 1, n):
            other_statement = ir.statements[j]
            if not isinstance(other_statement, Instruction):
                break

            other_qubit_indices = set(other_statement.qubit_indices)

            if inter := qubit_indices.intersection(other_qubit_indices):
                graph.add_edge(i, j, qubit_index=tuple(inter))
                qubit_indices = qubit_indices.difference(inter)

            if not qubit_indices:
                break

    graph = _add_asm_declaration_edges(graph, ir)

    if not nx.is_directed_acyclic_graph(graph):
        raise ValueError

    return graph


def group_gates(graph: nx.DiGraph) -> list[tuple[set[int], set[int]]]:
    groups: list[tuple[set, set]] = []
    available_nodes = set(graph.nodes)
    start_nodes = [n for n in graph.nodes if graph.in_degree(n) == 0]

    while start_nodes or available_nodes:
        if not start_nodes:
            start_nodes = [n for n in available_nodes if all(p not in available_nodes for p in graph.predecessors(n))]
        node = start_nodes.pop(0)
        if node not in available_nodes:
            continue

        qubit_indices = set(graph.nodes[node]["qubit_indices"])
        group = {node}
        available_nodes.remove(node)

        neighbors = list(graph.successors(node))
        while neighbors:
            neighbor = neighbors.pop(0)
            if neighbor not in available_nodes:
                continue

            neighbor_qubit_indices = set(graph.nodes[neighbor]["qubit_indices"])
            if len(qubit_indices) == 1:
                qubit_indices.update(neighbor_qubit_indices)

            if neighbor_qubit_indices.issubset(qubit_indices):
                group.add(neighbor)
                available_nodes.remove(neighbor)
                neighbors.extend(s for s in graph.successors(neighbor) if s in available_nodes)
                neighbors.extend(p for p in graph.predecessors(neighbor) if p in available_nodes)
            else:
                succ = list(graph.successors(neighbor))
                for s in succ:
                    if s in available_nodes and s in neighbors:
                        neighbors.remove(s)

        groups.append((group, qubit_indices))
    return sorted(groups, key=lambda x: _first_two_qubit_gate(graph, x[0]))


def _first_two_qubit_gate(graph: nx.DiGraph, group: set[int]) -> int:
    """Return the first statement index pointing to a two qubit gate."""
    x = [i for i in group if len(graph.nodes[i]["qubit_indices"]) == 2]
    return min(x) if x else min(group)


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
    for index in sorted(group):
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
