from typing import Any

import networkx as nx

from opensquirrel.ir import IR
from opensquirrel.passes.router.common import PathFinderType, ProcessSwaps
from opensquirrel.passes.router.general_router import Connectivity, Router


class ShortestPathRouter(Router):
    def __init__(self, connectivity: Connectivity, **kwargs: Any) -> None:
        super().__init__(connectivity, **kwargs)

    def route(self, ir: IR, qubit_register_size: int) -> IR:
        pathfinder: PathFinderType = nx.shortest_path
        return ProcessSwaps.process_swaps(ir, qubit_register_size, self._connectivity, pathfinder)
