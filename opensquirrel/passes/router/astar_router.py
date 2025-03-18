import math

import networkx as nx

from opensquirrel.exceptions import NoRoutingPathError
from opensquirrel.ir import IR, SWAP, Gate
from opensquirrel.passes.router import Router


class AStarRouter(Router):
    def __init__(self, connectivity: dict[str, list[int]], heuristic=None) -> None:  # type: ignore[no-untyped-def] # noqa: ANN001
        self.connectivity = connectivity
        self.heuristic = heuristic or (lambda a, b, num_columns: 0)

    def route(self, ir: IR) -> IR:
        """
        Routes the circuit by inserting SWAP gates to make it executable given the hardware connectivity.
        Args:
            ir: The intermediate representation of the circuit.
        Returns:
            The intermediate representation of the routed circuit (including the additional SWAP gates).
        """
        graph_data = {int(start_node): end_nodes for start_node, end_nodes in self.connectivity.items()}
        graph = nx.Graph(graph_data)
        num_qubits = max(graph.nodes) + 1
        num_columns = math.ceil(math.sqrt(num_qubits))
        statement_index = 0
        while statement_index < len(ir.statements):
            statement = ir.statements[statement_index]
            if isinstance(statement, Gate) and len(statement.get_qubit_operands()) == 2:
                q0, q1 = statement.get_qubit_operands()
                if not graph.has_edge(q0.index, q1.index):
                    try:
                        shortest_path = nx.astar_path(
                            graph,
                            source=q0.index,
                            target=q1.index,
                            heuristic=lambda u, v: self.heuristic(u, v, num_columns),
                        )
                        for start_qubit_index, end_qubit_index in zip(shortest_path[:-1], shortest_path[1:]):
                            ir.statements.insert(statement_index, SWAP(start_qubit_index, end_qubit_index))
                            statement_index += 1
                    except nx.NetworkXNoPath as e:
                        msg = f"No routing path available between qubit {q0.index} and qubit {q1.index}"
                        raise NoRoutingPathError(msg) from e
            statement_index += 1
        return ir
