from __future__ import annotations

import itertools
from collections.abc import Callable
from typing import TYPE_CHECKING

import networkx as nx

from opensquirrel import SWAP
from opensquirrel.exceptions import NoRoutingPathError
from opensquirrel.ir import IR, Gate, Instruction, Statement

if TYPE_CHECKING:
    from opensquirrel import Connectivity

PathFinderType = Callable[[nx.Graph, int, int], list[int]]


def get_graph(connectivity: Connectivity) -> nx.Graph:
    """Creates a networkx graph from the given connectivity.

    Args:
        connectivity (dict[str, list[int]]): Connectivity mapping of physical qubits.

    Returns:
        nx.Graph: Networkx graph from the given connectivity.

    """
    return nx.Graph({int(start): ends for start, ends in connectivity.items()})


def get_identity_mapping(qubit_register_size: int) -> dict[int, int]:
    """Creates an identity mapping.

    Args:
        qubit_register_size (int): The size of the qubit register.

    Returns:
        dict[int, int]: An identity mapping.

    """
    return {qubit_index: qubit_index for qubit_index in range(qubit_register_size)}


class ProcessSwaps:
    @staticmethod
    def process_swaps(
        ir: IR,
        qubit_register_size: int,
        connectivity: Connectivity,
        pathfinder: PathFinderType,
    ) -> IR:
        """Processes SWAPs as determined by the pathfinder algorithm.

        Args:
            ir (IR): The IR of the circuit.
            qubit_register_size (int): The size of the qubit register.
            connectivity (dict[str, list[int]]): Connectivity mapping of physical qubits.
            pathfinder (PathFinderType): The pathfinder algorithm.
        Returns:
            IR: IR with the SWAPs processed through.

        """
        graph = get_graph(connectivity)
        initial_mapping = get_identity_mapping(qubit_register_size)
        planned_swaps = ProcessSwaps._plan_swaps(ir, graph, initial_mapping, pathfinder)
        ir.statements = ProcessSwaps._apply_swaps(ir, planned_swaps, initial_mapping)
        return ir

    @staticmethod
    def _plan_swaps(
        ir: IR,
        graph: nx.Graph,
        initial_mapping: dict[int, int],
        pathfinder: PathFinderType,
    ) -> dict[int, SWAP]:
        """Traverses the IR and determines where SWAPs need to be placed.

        Args:
            ir (IR): The IR of the circuit.
            graph (nx.Graph): The NetworkX graph representation of the qubit connectivity.
            initial_mapping (dict[int, int]): The initial mapping of the qubits.
            pathfinder (Callable[[nx.Graph, int, int], list[int]]):
        Returns:
            dict[int, SWAP]: An mapping from the insert position to SWAP instruction.

        """
        planned_swaps: dict[int, SWAP] = {}
        temp_mapping = initial_mapping.copy()

        for statement_index, statement in enumerate(ir.statements):
            if isinstance(statement, Gate) and len(statement.get_qubit_operands()) == 2:
                q0, q1 = statement.get_qubit_operands()
                physical_q0_index = temp_mapping[q0.index]
                physical_q1_index = temp_mapping[q1.index]

                if not graph.has_edge(physical_q0_index, physical_q1_index):
                    try:
                        path = pathfinder(graph, physical_q0_index, physical_q1_index)
                    except nx.NetworkXNoPath as e:
                        msg = f"No routing path available between qubit {q0.index} and qubit {q1.index}"
                        raise NoRoutingPathError(msg) from e

                    base_offset = len(planned_swaps)

                    # Final edge of the path is skipped as those qubits are already neighbors.
                    swaps_for_path = itertools.pairwise(path[:-1])
                    for swap_count, swap_pair in enumerate(swaps_for_path):
                        insert_position = statement_index + base_offset + swap_count
                        planned_swaps[insert_position] = SWAP(*swap_pair)
                        ProcessSwaps._update_mapping_for_swap(temp_mapping, swap_pair)
        return planned_swaps

    @staticmethod
    def _apply_swaps(ir: IR, planned_swaps: dict[int, SWAP], initial_mapping: dict[int, int]) -> list[Statement]:
        """Insert planned SWAPs and update qubit indices.

        Args:
            ir (IR): The IR of the circuit.
            planned_swaps (dict[int, SWAP]): The mapping from the insert position to SWAP instruction.
            initial_mapping (dict[int, int]): The initial mapping of the qubits.
        Returns:
            list[Statement]: An updated list of IR Statements.

        """
        new_ir_statements: list[Statement] = []
        new_mapping = initial_mapping.copy()

        for statement in ir.statements:
            while len(new_ir_statements) in planned_swaps:
                swap_gate = planned_swaps[len(new_ir_statements)]
                swap_qubit_indices = tuple(qubit.index for qubit in swap_gate.get_qubit_operands())
                ProcessSwaps._update_mapping_for_swap(new_mapping, swap_qubit_indices)
                new_ir_statements.append(swap_gate)

            if isinstance(statement, Instruction):
                for qubit in statement.get_qubit_operands():
                    qubit.index = new_mapping[qubit.index]

            new_ir_statements.append(statement)
        return new_ir_statements

    @staticmethod
    def _update_mapping_for_swap(mapping: dict[int, int], swap_qubit_indices: tuple[int, ...]) -> None:
        """Updates the mapping for the given swap qubit indices.

        Args:
            mapping (dict[int, int]): The mapping of the qubit indices (logical qubit index: physical qubit index).
            swap_qubit_indices (tuple[int, int]): The swap qubit indices.

        """
        index_q0, index_q1 = swap_qubit_indices
        reverse_mapping = {value: key for key, value in mapping.items()}
        logical_index_q0, logical_index_q1 = reverse_mapping.get(index_q0), reverse_mapping.get(index_q1)
        if logical_index_q0 is not None:
            mapping[logical_index_q0] = index_q1
        if logical_index_q1 is not None:
            mapping[logical_index_q1] = index_q0
