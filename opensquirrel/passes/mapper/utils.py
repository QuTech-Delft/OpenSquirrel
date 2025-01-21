import networkx as nx

from opensquirrel.ir import IR, Gate


def make_interaction_graph(ir: IR) -> nx.Graph:
    interaction_graph = nx.Graph()
    gates = (statement for statement in ir.statements if isinstance(statement, Gate))

    for gate in gates:
        target_qubits = gate.get_qubit_operands()
        if len(target_qubits) == 1:
            continue
        if len(target_qubits) > 2:
            msg = (
                f"the gate {gate} acts on more than 2 qubits. "
                "The gate must be decomposed before an interaction graph can be made",
            )
            raise ValueError(msg)
        interaction_graph.add_edge(*target_qubits)

    return interaction_graph
