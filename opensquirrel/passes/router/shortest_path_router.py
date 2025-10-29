from typing import Any

import networkx as nx

from opensquirrel.ir import IR
from opensquirrel.passes.router.common import (
    apply_swaps,
    build_graph,
    identity_mapping,
    plan_swaps,
)
from opensquirrel.passes.router.general_router import Router


class ShortestPathRouter(Router):
    def __init__(self, connectivity: dict[str, list[int]], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.connectivity = connectivity
        self._graph = build_graph(self.connectivity)  # type: ignore  [arg-type]
        self._initial_mapping: dict[int, int] | None = None
        self._ir: IR | None = None

    def route(self, ir: IR, qubit_register_size: int) -> IR:
        self._ir = ir
        self._initial_mapping = identity_mapping(qubit_register_size)

        swaps_to_insert = plan_swaps(
            ir=self._ir,
            graph=self._graph,
            initial_mapping=self._initial_mapping,
            find_path=lambda g, s, d: list(nx.shortest_path(g, source=s, target=d)),
        )

        self._ir.statements = apply_swaps(self._ir, swaps_to_insert, self._initial_mapping)
        return self._ir
