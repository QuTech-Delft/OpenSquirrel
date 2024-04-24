from __future__ import annotations

from abc import ABC, abstractmethod

import networkx as nx

from opensquirrel.squirrel_ir import ControlledGate, Gate, Measure, SquirrelIR


def map_qubits(squirrel_ir: SquirrelIR, mapper: type[Mapper], *args, **kwargs) -> None:

    mapping = mapper.map(squirrel_ir, *args, **kwargs)

    for statement in squirrel_ir.statements:
        if isinstance(statement, (Gate, Measure)):
            statement.relabel(mapping)


def make_interaction_graph(squirrel_ir: SquirrelIR) -> nx.Graph:
    interaction_graph = nx.Graph()
    controlled_gates = (statement for statement in squirrel_ir.statements if isinstance(statement, ControlledGate))

    for gate in controlled_gates:
        target_qubits = gate.target_gate.get_qubit_operands()
        if len(target_qubits) > 1:
            raise ValueError(
                f"The ControlledGate {gate} has multiple target qubits. These must be  decomposed before creating an "
                "interaction graph."
            )

        interaction = (gate.control_qubit, target_qubits[0])
        interaction_graph.add_edge(interaction)

    return interaction_graph


class Mapper(ABC):

    @abstractmethod
    def map(self, squirrel_ir: SquirrelIR, *args, **kwargs) -> dict[int, int]:
        """Note that the mapper should *not* alter `squirrel_ir`."""
