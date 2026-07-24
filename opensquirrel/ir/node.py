from __future__ import annotations

from opensquirrel.ir import IR, Instruction, AsmDeclaration
from opensquirrel.ir.single_qubit_gate import SingleQubitGate
from opensquirrel.ir.two_qubit_gate import TwoQubitGate
from collections import deque
from opensquirrel.ir.statement import Statement
from dataclasses import dataclass, field

import networkx as nx

def build_graph(ir: IR) -> nx.DiGraph:
    n = len(ir.statements)
    graph = nx.DiGraph()
    graph.add_nodes_from(range(n))

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
            

def f(graph: nx.DiGraph):
    qubit_indices = nx.get_edge_attributes(graph, "qubit_index", default=None)

