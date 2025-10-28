from __future__ import annotations

import math
from typing import Any, Mapping

import networkx as nx

from opensquirrel import SWAP
from opensquirrel.exceptions import NoRoutingPathError
from opensquirrel.ir import IR, Gate, Instruction, Statement
from opensquirrel.passes.router.general_router import Router
from opensquirrel.passes.router.heuristics import DistanceMetric, calculate_distance


class AStarRouter(Router):
    def __init__(
        self, connectivity: dict[str, list[int]], distance_metric: DistanceMetric | None = None, **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)
        self.connectivity = connectivity
        self.distance_metric = distance_metric

    def _get_swaps_for_path(self, path: list[int]) -> list[tuple[int, int]]:
        """Generate SWAP pairs for a path."""
        # We need len(path) - 2. After this, the two qubits are neighbors on the final edge.
        return [(path[i], path[i + 1]) for i in range(len(path) - 2)]

    def _build_graph(self) -> nx.Graph:
        graph_data = {int(start_node): end_nodes for start_node, end_nodes in self.connectivity.items()}
        return nx.Graph(graph_data)    

    def _init_qubit_mapping(self, qubit_register_size: int) -> dict[int, int]:
        # Start with an identity mapping.
        return {
            logical_index: virtual_index
            for logical_index, virtual_index in zip(
                list(range(qubit_register_size)), list(range(qubit_register_size))
            )
        }

    def _update_mapping_for_swap(self, mapping: dict[int, int], swap_pair: tuple[int, int]) -> None:
        # Given a physical swap (a <-> b), update which logical qubits currently occupy a and b.
        a, b = swap_pair
        logical_a = None
        logical_b = None
        for logical, physical in mapping.items():
            if physical == a:
                logical_a = logical
            elif physical == b:
                logical_b = logical
        if logical_a is not None:
            mapping[logical_a] = b
        if logical_b is not None:
            mapping[logical_b] = a

    def _astar_path(self, graph: nx.Graph, src: int, dst: int) -> list[int]:
        # Use A* with optional heuristic
        if self.distance_metric is None:
            return list(nx.astar_path(graph, source=src, target=dst))
        num_available_qubits = max(graph.nodes) + 1
        num_columns = math.ceil(math.sqrt(num_available_qubits))
        return list(
            nx.astar_path(
                graph,
                source=src,
                target=dst,
                heuristic=lambda u, v: calculate_distance(u, v, num_columns, self.distance_metric),
            )
        )

    def _plan_swaps(self, ir: IR, graph: nx.Graph, initial_mapping: Mapping[int, int]) -> list[tuple[int, SWAP]]:
        # Go through the IR and see where SWAPs need to be placed.
        swaps_to_insert: list[tuple[int, SWAP]] = []
        # Copy so planning doesn’t mutate the baseline used by the construction phase.
        temp_mapping: dict[int, int] = dict(initial_mapping)

        for statement_idx, statement in enumerate(ir.statements):
            if isinstance(statement, Gate) and len(statement.get_qubit_operands()) == 2:
                q0, q1 = statement.get_qubit_operands()
                physical_q0_index = temp_mapping[q0.index]
                physical_q1_index = temp_mapping[q1.index]

                if not graph.has_edge(physical_q0_index, physical_q1_index):
                    try:
                        path = self._astar_path(graph, physical_q0_index, physical_q1_index)
                    except nx.NetworkXNoPath as e:
                        msg = f"No routing path available between qubit {q0.index} and qubit {q1.index}"
                        raise NoRoutingPathError(msg) from e

                    for swap_pair in self._get_swaps_for_path(path):
                        # Account for earlier planned inserts shifting indices.
                        insert_position = statement_idx + len(swaps_to_insert)
                        swaps_to_insert.append((insert_position, SWAP(swap_pair[0], swap_pair[1])))
                        # Simulate the swap effect for subsequent gates in planning.
                        self._update_mapping_for_swap(temp_mapping, swap_pair)

        return swaps_to_insert

    def _apply_swaps(
        self, ir: IR, swaps_to_insert: list[tuple[int, SWAP]], initial_mapping: dict[int, int]
    ) -> list[Statement]:
        # Insert planned SWAPs and update qubit indices
        new_statements: list[Statement] = []
        swap_index = 0
        total_swaps = len(swaps_to_insert)
        final_mapping = dict(initial_mapping)

        for _, statement in enumerate(ir.statements):
            while swap_index < total_swaps and swaps_to_insert[swap_index][0] == len(new_statements):
                swap_gate = swaps_to_insert[swap_index][1]
                new_statements.append(swap_gate)

                swap_qubits = swap_gate.get_qubit_operands()
                swap_pair = (swap_qubits[0].index, swap_qubits[1].index)
                self._update_mapping_for_swap(final_mapping, swap_pair)

                swap_index += 1

            if isinstance(statement, Instruction):
                for qubit in statement.get_qubit_operands():
                    qubit.index = final_mapping[qubit.index]

            new_statements.append(statement)

        while swap_index < total_swaps:
            new_statements.append(swaps_to_insert[swap_index][1])
            swap_index += 1

        return new_statements

    def route(self, ir: IR, qubit_register_size: int) -> IR:
        """
        Routes the circuit by inserting SWAP gates (via A*) to satisfy hardware connectivity.
        """
        graph = self._build_graph()
        initial_mapping = self._init_qubit_mapping(qubit_register_size)
        swaps_to_insert = self._plan_swaps(ir, graph, initial_mapping)
        ir.statements = self._apply_swaps(ir, swaps_to_insert, initial_mapping)
        return ir
