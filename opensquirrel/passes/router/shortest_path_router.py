import networkx as nx

from opensquirrel.ir import IR, SWAP, Gate, Qubit
from opensquirrel.passes.router import Router


class ShortestPathRouter(Router):
    def __init__(self, connectivity_scheme: dict[int, list[int]]) -> None:
        self.connectivity_scheme = connectivity_scheme

    def route(self, ir: IR) -> IR:
        """
        Routes the given intermediate representation (IR) by inserting SWAP gates
        to make the circuit executable on the given hardware connectivity scheme.

        Args:
            ir (IR): The intermediate representation of the circuit to be routed.

        Returns:
            new_ir (IR): The new intermediate representation with the additional SWAP gates.
        """
        graph = nx.Graph(self.connectivity_scheme)
        new_ir = IR()
        for statement in ir.statements:
            if isinstance(statement, Gate) and len(statement.get_qubit_operands()) == 2:
                q0, q1 = statement.get_qubit_operands()
                if not graph.has_edge(q0.index, q1.index):
                    try:
                        shortest_path = nx.shortest_path(graph, source=q0.index, target=q1.index)
                        for i, j in zip(shortest_path[:-1], shortest_path[1:]):
                            new_ir.add_gate(SWAP(Qubit(i), Qubit(j)))
                    except nx.NetworkXNoPath:
                        print(f"No path between {q0.index} and {q1.index}")  # noqa: T201
            new_ir.add_statement(statement)
        return new_ir
