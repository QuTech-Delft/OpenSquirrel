from typing import Any

import networkx as nx

from opensquirrel import Connectivity
from opensquirrel.ir import IR
from opensquirrel.passes.router.common import PathFinderType, ProcessSwaps
from opensquirrel.passes.router.general_router import Router


class ShortestPathRouter(Router):
    def __init__(self, connectivity: Connectivity, **kwargs: Any) -> None:
        super().__init__(connectivity, **kwargs)

    def route(self, ir: IR, qubit_register_size: int) -> IR:
        """Route the input IR using the [shortest-path](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.shortest_paths.generic.shortest_path.html)
        search algorithm.

        Args:
            ir (IR): The input IR to be routed.
            qubit_register_size (int): Size of the qubit register.

        Returns:
            The routed IR.

        """
        pathfinder: PathFinderType = nx.shortest_path
        return ProcessSwaps.process_swaps(ir, qubit_register_size, self._connectivity, pathfinder)
