from __future__ import annotations

from collections.abc import Callable, Mapping

import networkx as nx

from opensquirrel import SWAP
from opensquirrel.exceptions import NoRoutingPathError
from opensquirrel.ir import IR, Gate, Instruction, Statement


def build_graph(connectivity: Mapping[int | str, list[int]]) -> nx.Graph:
    graph_data = {int(start): list(map(int, ends)) for start, ends in connectivity.items()}
    return nx.Graph(graph_data)


def identity_mapping(qubit_register_size: int) -> dict[int, int]:
    # Start with an identity mapping.
    return {i: i for i in range(qubit_register_size)}


def update_mapping_for_swap(mapping: dict[int, int], swap_pair: tuple[int, int]) -> None:
    # Given a physical swap (a <-> b), update which logical qubits currently occupy a and b
    a, b = swap_pair
    reverse_mapping = {v: k for k, v in mapping.items()}
    logical_a = reverse_mapping.get(a)
    logical_b = reverse_mapping.get(b)
    if logical_a is not None:
        mapping[logical_a] = b
    if logical_b is not None:
        mapping[logical_b] = a


def get_swaps_for_path(path: list[int]) -> list[tuple[int, int]]:
    # We need len(path) - 2. After this, the two qubits are neighbors on the final edge.
    return [(path[i], path[i + 1]) for i in range(len(path) - 2)]


def apply_swaps(ir: IR, swaps_to_insert: list[tuple[int, SWAP]], initial_mapping: dict[int, int]) -> list[Statement]:
    # Insert planned SWAPs and update qubit indices
    new_statements: list[Statement] = []
    swap_index = 0
    total_swaps = len(swaps_to_insert)
    new_mapping = dict(initial_mapping)

    for statement in ir.statements:
        while swap_index < total_swaps and swaps_to_insert[swap_index][0] == len(new_statements):
            swap_gate = swaps_to_insert[swap_index][1]
            new_statements.append(swap_gate)
            swap_pair = tuple(qubit.index for qubit in swap_gate.get_qubit_operands())
            update_mapping_for_swap(new_mapping, swap_pair)  # type: ignore  [arg-type]
            swap_index += 1

        if isinstance(statement, Instruction):
            for qubit in statement.get_qubit_operands():
                qubit.index = new_mapping[qubit.index]

        new_statements.append(statement)

    return new_statements


def plan_swaps(
    ir: IR,
    graph: nx.Graph,
    initial_mapping: Mapping[int, int],
    find_path: Callable[[nx.Graph, int, int], list[int]],
) -> list[tuple[int, SWAP]]:
    # Go through the IR and see where SWAPs need to be placed.
    swaps_to_insert: list[tuple[int, SWAP]] = []
    temp_mapping: dict[int, int] = dict(initial_mapping)

    for statement_idx, statement in enumerate(ir.statements):
        if isinstance(statement, Gate) and len(statement.get_qubit_operands()) == 2:
            q0, q1 = statement.get_qubit_operands()
            physical_q0_index = temp_mapping[q0.index]
            physical_q1_index = temp_mapping[q1.index]

            if not graph.has_edge(physical_q0_index, physical_q1_index):
                try:
                    path = find_path(graph, physical_q0_index, physical_q1_index)
                except nx.NetworkXNoPath as e:
                    msg = f"No routing path available between qubit {q0.index} and qubit {q1.index}"
                    raise NoRoutingPathError(msg) from e

                base_offset = len(swaps_to_insert)
                for swap_count, swap_pair in enumerate(get_swaps_for_path(path)):
                    insert_position = statement_idx + base_offset + swap_count
                    swaps_to_insert.append((insert_position, SWAP(*swap_pair)))
                    update_mapping_for_swap(temp_mapping, swap_pair)

    return swaps_to_insert
