from typing import Any

import networkx as nx

from opensquirrel import SWAP
from opensquirrel.exceptions import NoRoutingPathError
from opensquirrel.ir import IR, Gate, Instruction, Statement
from opensquirrel.passes.router.general_router import Router


class ShortestPathRouter(Router):
    def __init__(self, connectivity: dict[str, list[int]], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.connectivity = connectivity

    def _get_swaps_for_path(self, shortest_path: list[int]) -> list[tuple[int, int]]:
        """Generate SWAP pairs for a shortest path."""
        # We need len(path) - 2. After this, the two qubits are neighbors on the final edge.
        return [(shortest_path[i], shortest_path[i + 1]) for i in range(len(shortest_path) - 2)]

    def _build_graph(self) -> nx.Graph:
        graph_data = {int(start_node): end_nodes for start_node, end_nodes in self.connectivity.items()}
        return nx.Graph(graph_data)

    def _init_qubit_mapping(self, ir: IR) -> dict[int, int]:
        # Start with an identity mapping
        mapping: dict[int, int] = {}
        for statement in ir.statements:
            if isinstance(statement, Instruction):
                for qubit in statement.get_qubit_operands():
                    if qubit.index not in mapping:
                        mapping[qubit.index] = qubit.index
        return mapping

    def _update_mapping_for_swap(self, mapping: dict[int, int], swap_pair: tuple[int, int]) -> None:
        # Given a physical swap (a <-> b), update which logical qubits currently occupy a and b.
        a, b = swap_pair
        logical_a = None
        logical_b = None
        for logical, physical in mapping.items():
            if physical == a:
                logical_a = logical
            elif physical == b:
                logical_b = logical
        if logical_a is not None:
            mapping[logical_a] = b
        if logical_b is not None:
            mapping[logical_b] = a

    def _plan_swaps(self, ir: IR, graph: nx.Graph, initial_mapping: dict[int, int]) -> list[tuple[int, SWAP]]:
        # Go through the IR and see where SWAPs need to be placed.
        swaps_to_insert: list[tuple[int, SWAP]] = []
        temp_mapping = dict(initial_mapping)

        for statement_idx, statement in enumerate(ir.statements):
            if isinstance(statement, Gate) and len(statement.get_qubit_operands()) == 2:
                q0, q1 = statement.get_qubit_operands()
                physical_q0 = temp_mapping[q0.index]
                physical_q1 = temp_mapping[q1.index]

                if not graph.has_edge(physical_q0, physical_q1):
                    try:
                        shortest_path = nx.shortest_path(graph, source=physical_q0, target=physical_q1)
                    except nx.NetworkXNoPath as e:
                        msg = f"No routing path available between qubit {q0.index} and qubit {q1.index}"
                        raise NoRoutingPathError(msg) from e

                    for swap_pair in self._get_swaps_for_path(shortest_path):
                        insert_position = statement_idx + len(swaps_to_insert)
                        swaps_to_insert.append((insert_position, SWAP(swap_pair[0], swap_pair[1])))
                        self._update_mapping_for_swap(temp_mapping, swap_pair)

        return swaps_to_insert

    def _apply_swaps(
        self, ir: IR, swaps_to_insert: list[tuple[int, SWAP]], initial_mapping: dict[int, int]
    ) -> list[Statement]:
        # Insert planned SWAPs and update qubit indices
        new_statements: list[Statement] = []
        swap_index = 0
        total_swaps = len(swaps_to_insert)
        final_mapping = dict(initial_mapping)

        for _, statement in enumerate(ir.statements):
            while swap_index < total_swaps and swaps_to_insert[swap_index][0] == len(new_statements):
                swap_gate = swaps_to_insert[swap_index][1]
                new_statements.append(swap_gate)

                swap_qubits = swap_gate.get_qubit_operands()
                swap_pair = (swap_qubits[0].index, swap_qubits[1].index)
                self._update_mapping_for_swap(final_mapping, swap_pair)

                swap_index += 1

            if isinstance(statement, Instruction):
                for qubit in statement.get_qubit_operands():
                    qubit.index = final_mapping[qubit.index]

            new_statements.append(statement)

        while swap_index < total_swaps:
            new_statements.append(swaps_to_insert[swap_index][1])
            swap_index += 1

        return new_statements

    def route(self, ir: IR) -> IR:
        """
        Routes the circuit by inserting SWAP gates along the shortest path between qubits which can not
        interact with each other, to make it executable given the hardware connectivity.
        """
        graph = self._build_graph()
        initial_mapping = self._init_qubit_mapping(ir)
        swaps_to_insert = self._plan_swaps(ir, graph, initial_mapping)
        ir.statements = self._apply_swaps(ir, swaps_to_insert, initial_mapping)
        return ir
