import math
from typing import Any

import networkx as nx

from opensquirrel.ir import IR
from opensquirrel.passes.router.common import PathFinderType, ProcessSwaps
from opensquirrel.passes.router.general_router import Connectivity, Router
from opensquirrel.passes.router.heuristics import DistanceMetric, calculate_distance


class AStarRouter(Router):
    def __init__(
        self, connectivity: Connectivity, distance_metric: DistanceMetric | None = None, **kwargs: Any
    ) -> None:
        super().__init__(connectivity, **kwargs)
        self._distance_metric = distance_metric

    def route(self, ir: IR, qubit_register_size: int) -> IR:
        pathfinder: PathFinderType = self._astar_pathfinder
        return ProcessSwaps.process_swaps(ir, qubit_register_size, self._connectivity, pathfinder)

    def _astar_pathfinder(self, graph: nx.Graph, source: int, target: int) -> Any:
        num_available_qubits = max(graph.nodes) + 1
        num_columns = math.ceil(math.sqrt(num_available_qubits))
        return nx.astar_path(
            graph,
            source=source,
            target=target,
            heuristic=lambda q0_index, q1_index: calculate_distance(
                q0_index, q1_index, num_columns, self._distance_metric
            )
            if self._distance_metric
            else None,
        )
