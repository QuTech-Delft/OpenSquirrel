import networkx as nx

from opensquirrel.squirrel_ir import Gate, SquirrelIR


def make_interaction_graph(squirrel_ir: SquirrelIR) -> nx.Graph:

    interaction_graph = nx.Graph()
    gates = (statement for statement in squirrel_ir.statements if isinstance(statement, Gate))

    for gate in gates:
        target_qubits = gate.get_qubit_operands()
        if len(target_qubits) == 1:
            continue
        if len(target_qubits) > 2:
            raise ValueError(
                f"The gate {gate} acts on more than 2 qubits. The gate must be decomposed before an interaction graph "
                "can be made."
            )
        interaction_graph.add_edge(*target_qubits)

    return interaction_graph
