from __future__ import annotations

from itertools import chain
from typing import TYPE_CHECKING

import networkx as nx
import numpy as np

from opensquirrel.circuit_builder import CircuitBuilder
from opensquirrel.circuit_matrix_calculator import get_circuit_matrix
from opensquirrel.ir import IR, ControlInstruction, Gate, Instruction, Qubit
from opensquirrel.ir.default_gates.two_qubit_gates import SWAP
from opensquirrel.ir.non_unitary import NonUnitary
from opensquirrel.ir.semantics.matrix_gate import MatrixGateSemantic
from opensquirrel.ir.single_qubit_gate import SingleQubitGate
from opensquirrel.ir.statement import AsmDeclaration
from opensquirrel.ir.two_qubit_gate import TwoQubitGate
from opensquirrel.passes.merger.general_merger import Merger

if TYPE_CHECKING:
    from opensquirrel.circuit import Circuit


Group = tuple[set[int], set[int]]  # (statement indices, qubit indices)

SWAP_MATRIX = SWAP(0, 1).matrix


def build_graph(ir: IR) -> nx.DiGraph:
    n = len(ir.statements)
    graph = nx.DiGraph()
    graph.add_nodes_from(
        (i, {"qubit_indices": set(statement.qubit_indices) if isinstance(statement, Instruction) else set(range(n))})
        for i, statement in enumerate(ir.statements)
    )

    for i in range(n):
        qubit_indices = graph.nodes[i]["qubit_indices"]

        for j in range(i + 1, n):
            other_qubit_indices = graph.nodes[j]["qubit_indices"]

            if inter := qubit_indices.intersection(other_qubit_indices):
                graph.add_edge(i, j, qubit_index=tuple(inter))
                qubit_indices = qubit_indices.difference(inter)

    for node in graph.nodes:
        if isinstance(ir.statements[node], (NonUnitary, AsmDeclaration, ControlInstruction)):
            graph.nodes[node]["qubit_indices"] = None

    if not nx.is_directed_acyclic_graph(graph):
        raise ValueError

    return graph


def get_starting_nodes(graph: nx.DiGraph, available_nodes: set[int] | None = None) -> list[int]:
    if available_nodes is None:
        available_nodes = set(graph.nodes)
    return [n for n, degree in graph.subgraph(available_nodes).in_degree() if degree == 0]


def group_gates(graph: nx.DiGraph) -> list[Group]:
    groups: list[Group] = []
    available_nodes = set(graph.nodes)
    start_nodes = get_starting_nodes(graph)

    while start_nodes or available_nodes:
        if not start_nodes:
            start_nodes = get_starting_nodes(graph, available_nodes)
        node = start_nodes.pop(0)
        if node not in available_nodes:
            continue

        group = {node}
        available_nodes.remove(node)
        bad_indices = set()
        if graph.nodes[node]["qubit_indices"] is None:
            start_nodes.extend(graph.successors(node))
            groups.append((group, set()))
            available_nodes.remove(node)
            continue

        qubit_indices = set(graph.nodes[node]["qubit_indices"])
        neighbors = list(graph.successors(node))
        while neighbors:
            neighbor = neighbors.pop(0)
            if neighbor not in available_nodes:
                continue

            if graph.nodes[neighbor]["qubit_indices"] is None:
                start_nodes.extend(graph.successors(neighbor))
                groups.append(({neighbor}, set()))
                available_nodes.remove(neighbor)
                continue

            neighbor_qubit_indices = set(graph.nodes[neighbor]["qubit_indices"])
            if len(qubit_indices) == 1:
                qubit_indices.update(neighbor_qubit_indices)

            if neighbor_qubit_indices <= qubit_indices and not bad_indices & neighbor_qubit_indices:
                group.add(neighbor)
                available_nodes.remove(neighbor)
                neighbors.extend(
                    n for n in chain(graph.successors(neighbor), graph.predecessors(neighbor)) if n in available_nodes
                )
            else:
                bad_indices |= neighbor_qubit_indices & qubit_indices

        groups.append((group, qubit_indices))
    return sorted(groups, key=lambda x: _first_two_qubit_gate(graph, x))


def _first_two_qubit_gate(graph: nx.DiGraph, group: Group) -> int:
    """Return the first statement index pointing to a two qubit gate."""
    statement_indices, qubit_indices = group
    if not qubit_indices:
        return min(statement_indices)

    x = [i for i in statement_indices if len(graph.nodes[i]["qubit_indices"]) == 2]
    return min(x) if x else min(statement_indices)


def normalize_gate_indices(gate: Gate, mapping: dict[int, int]) -> Gate:
    if isinstance(gate, TwoQubitGate):
        gate.qubit0 = Qubit(mapping[gate.qubit0.index])
        gate.qubit1 = Qubit(mapping[gate.qubit1.index])
        return gate

    if isinstance(gate, SingleQubitGate):
        gate.qubit = Qubit(mapping[gate.qubit.index])
        return gate

    msg = f"Unsupported gate type: {type(gate)}"
    raise TypeError(msg)


def _merge_gate_group(ir: IR, group: Group) -> TwoQubitGate:
    statement_indices, qubit_indices = group
    index_mapping = {index: i for i, index in enumerate(sorted(qubit_indices))}
    builder = CircuitBuilder(len(qubit_indices))
    for index in sorted(statement_indices):
        statement = ir.statements[index]
        if isinstance(statement, Gate):
            statement = normalize_gate_indices(statement, index_mapping)
            builder.add_instruction(statement)

    sub_circuit_matrix = _get_sub_circuit_matrix(builder.to_circuit())
    return TwoQubitGate(*qubit_indices, gate_semantic=MatrixGateSemantic(sub_circuit_matrix))


def _get_sub_circuit_matrix(circuit: Circuit) -> np.ndarray:
    if circuit.qubit_register_size == 1:
        return get_circuit_matrix(circuit)
    # `get_circuit_matrix` uses the convention of the first qubit being the most significant bit,
    # so we need to swap the qubits before and after calculating the matrix
    return SWAP_MATRIX @ get_circuit_matrix(circuit) @ SWAP_MATRIX


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
        statements = []

        for group in groups:
            statement_indices, qubit_indices = group
            if len(qubit_indices) == 2 and len(statement_indices) > 1:
                merged_gate = _merge_gate_group(ir, group)
                statements.append(merged_gate)
            else:
                statements.append(ir.statements[statement_indices.pop()])

        ir.statements = statements
