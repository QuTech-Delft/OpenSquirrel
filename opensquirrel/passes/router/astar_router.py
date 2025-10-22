from __future__ import annotations

import math
from typing import Any

import networkx as nx

from opensquirrel import SWAP
from opensquirrel.exceptions import NoRoutingPathError
from opensquirrel.ir import IR, Gate, Instruction
from opensquirrel.passes.router.general_router import Router
from opensquirrel.passes.router.heuristics import DistanceMetric, calculate_distance


class AStarRouter(Router):
    def __init__(
        self, connectivity: dict[str, list[int]], distance_metric: DistanceMetric | None = None, **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)
        self.connectivity = connectivity
        self.distance_metric = distance_metric

    def _get_swaps_for_path(self, shortest_path: list[int]) -> list[tuple[int, int]]:
        """Generate SWAP pairs for a shortest path."""
        return [(shortest_path[i], shortest_path[i + 1]) for i in range(len(shortest_path) - 2)]

    def route(self, ir: IR) -> IR:
        """
        Routes the circuit by inserting SWAP gates, with A*, to make it executable given the hardware connectivity.
        Args:
            ir: The intermediate representation of the circuit.
        Returns:
            The intermediate representation of the routed circuit (including the additional SWAP gates).
        """
        graph_data = {int(start_node): end_nodes for start_node, end_nodes in self.connectivity.items()}
        graph = nx.Graph(graph_data)
        num_available_qubits = max(graph.nodes) + 1
        num_columns = math.ceil(math.sqrt(num_available_qubits))

        qubit_mapping = {}
        for statement in ir.statements:
            if isinstance(statement, Instruction):
                for qubit in statement.get_qubit_operands():
                    if qubit.index not in qubit_mapping:
                        qubit_mapping[qubit.index] = qubit.index

        swaps_to_insert = []
        temp_mapping = qubit_mapping.copy()

        for statement_idx, statement in enumerate(ir.statements):
            if isinstance(statement, Gate) and len(statement.get_qubit_operands()) == 2:
                q0, q1 = statement.get_qubit_operands()
                physical_q0 = temp_mapping[q0.index]
                physical_q1 = temp_mapping[q1.index]

                if not graph.has_edge(physical_q0, physical_q1):
                    try:
                        if self.distance_metric is None:
                            shortest_path = nx.astar_path(graph, source=physical_q0, target=physical_q1)
                        else:
                            shortest_path = nx.astar_path(
                                graph,
                                source=physical_q0,
                                target=physical_q1,
                                heuristic=lambda u, v: calculate_distance(u, v, num_columns, self.distance_metric),
                            )

                        swaps = self._get_swaps_for_path(shortest_path)

                        for swap_pair in swaps:
                            insert_position = statement_idx + len(swaps_to_insert)
                            swaps_to_insert.append((insert_position, SWAP(swap_pair[0], swap_pair[1])))

                            logical_at_start = None
                            logical_at_end = None
                            for logical, physical in temp_mapping.items():
                                if physical == swap_pair[0]:
                                    logical_at_start = logical
                                elif physical == swap_pair[1]:
                                    logical_at_end = logical

                            if logical_at_start is not None:
                                temp_mapping[logical_at_start] = swap_pair[1]
                            if logical_at_end is not None:
                                temp_mapping[logical_at_end] = swap_pair[0]

                    except nx.NetworkXNoPath as e:
                        msg = f"No routing path available between qubit {q0.index} and qubit {q1.index}"
                        raise NoRoutingPathError(msg) from e

        new_statements = []
        swap_index = 0
        final_mapping = qubit_mapping.copy()

        for _statement_idx, statement in enumerate(ir.statements):

            while swap_index < len(swaps_to_insert) and swaps_to_insert[swap_index][0] == len(new_statements):
                swap_gate = swaps_to_insert[swap_index][1]
                new_statements.append(swap_gate)

                swap_qubits = swap_gate.get_qubit_operands()
                swap_pair = (swap_qubits[0].index, swap_qubits[1].index)

                logical_at_start = None
                logical_at_end = None
                for logical, physical in final_mapping.items():
                    if physical == swap_pair[0]:
                        logical_at_start = logical
                    elif physical == swap_pair[1]:
                        logical_at_end = logical

                if logical_at_start is not None:
                    final_mapping[logical_at_start] = swap_pair[1]
                if logical_at_end is not None:
                    final_mapping[logical_at_end] = swap_pair[0]

                swap_index += 1

            if isinstance(statement, Instruction):
                for qubit in statement.get_qubit_operands():
                    qubit.index = final_mapping[qubit.index]

            new_statements.append(statement)

        while swap_index < len(swaps_to_insert):
            new_statements.append(swaps_to_insert[swap_index][1])
            swap_index += 1

        ir.statements = new_statements

        return ir
