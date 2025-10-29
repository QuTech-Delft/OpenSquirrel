from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

import networkx as nx

from opensquirrel.passes.router.common import (
    apply_swaps,
    build_graph,
    identity_mapping,
    plan_swaps,
)
from opensquirrel.passes.router.general_router import Router
from opensquirrel.passes.router.heuristics import DistanceMetric, calculate_distance

if TYPE_CHECKING:
    from opensquirrel.ir import IR


class AStarRouter(Router):
    def __init__(
        self, connectivity: dict[str, list[int]], distance_metric: DistanceMetric | None = None, **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)
        self.connectivity = connectivity
        self.distance_metric = distance_metric
        self._graph = build_graph(self.connectivity)  # type: ignore  [arg-type]
        self._initial_mapping: dict[int, int] | None = None
        self._ir: IR | None = None

    def _astar_path(self, graph: nx.Graph, src: int, dst: int) -> list[int]:
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

    def route(self, ir: IR, qubit_register_size: int) -> IR:
        self._ir = ir
        self._initial_mapping = identity_mapping(qubit_register_size)

        swaps_to_insert = plan_swaps(
            ir=self._ir,
            graph=self._graph,
            initial_mapping=self._initial_mapping,
            find_path=lambda g, s, d: self._astar_path(g, s, d),
        )

        self._ir.statements = apply_swaps(self._ir, swaps_to_insert, self._initial_mapping)
        return self._ir
