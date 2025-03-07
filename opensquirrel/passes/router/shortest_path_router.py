import networkx as nx

from opensquirrel.ir import IR, SWAP, Gate
from opensquirrel.passes.router import Router


class ShortestPathRouter(Router):
    def __init__(self, connectivity: dict[str, list[int]]) -> None:
        self.connectivity = connectivity

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
        instruction_counter = 0
        while instruction_counter < len(ir.statements):
            statement = ir.statements[instruction_counter]
            if isinstance(statement, Gate) and len(statement.get_qubit_operands()) == 2:
                q0, q1 = statement.get_qubit_operands()
                if not graph.has_edge(q0.index, q1.index):
                    try:
                        shortest_path = nx.shortest_path(graph, source=q0.index, target=q1.index)
                        for start_qubit_index, end_qubit_index in zip(shortest_path[:-1], shortest_path[1:]):
                            ir.statements.insert(instruction_counter, SWAP(start_qubit_index, end_qubit_index))
                            instruction_counter += 1
                    except nx.NetworkXNoPath:
                        print(f"No routing path available between qubit {q0.index} and qubit {q1.index}")  # noqa: T201
            instruction_counter += 1
        return ir
