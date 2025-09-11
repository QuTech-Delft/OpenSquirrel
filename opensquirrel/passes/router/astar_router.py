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

    def _insert_and_propagate_swaps(self, ir: IR, statement_index: int, shortest_path: list[int]) -> None:
        for start_qubit_index, end_qubit_index in zip(shortest_path[:-2], shortest_path[1:-1]):
            ir.statements.insert(statement_index, SWAP(start_qubit_index, end_qubit_index))
            # Update subsequent statements to reflect the swap
            for statement in ir.statements[statement_index + 1 :]:
                if isinstance(statement, Instruction):
                    for qubit in statement.get_qubit_operands():
                        if qubit.index == start_qubit_index:
                            qubit.index = end_qubit_index
                        elif qubit.index == end_qubit_index:
                            qubit.index = start_qubit_index
            statement_index += 1

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
        statement_index = 0
        while statement_index < len(ir.statements):
            statement = ir.statements[statement_index]
            if isinstance(statement, Gate) and len(statement.get_qubit_operands()) == 2:
                q0, q1 = statement.get_qubit_operands()
                if not graph.has_edge(q0.index, q1.index):
                    try:
                        if self.distance_metric is None:
                            shortest_path = nx.astar_path(graph, source=q0.index, target=q1.index)
                        else:
                            shortest_path = nx.astar_path(
                                graph,
                                source=q0.index,
                                target=q1.index,
                                heuristic=lambda u, v: calculate_distance(u, v, num_columns, self.distance_metric),
                            )
                        # -2 because we skip inserting a swap for the last edge in the path:
                        # len(path) - 1 edges in total
                        num_swaps_inserted = len(shortest_path) - 2
                        self._insert_and_propagate_swaps(ir, statement_index, shortest_path)
                        statement_index += num_swaps_inserted
                    except nx.NetworkXNoPath as e:
                        msg = f"No routing path available between qubit {q0.index} and qubit {q1.index}"
                        raise NoRoutingPathError(msg) from e
            statement_index += 1
        return ir
