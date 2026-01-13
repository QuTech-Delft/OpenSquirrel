import networkx as nx

from opensquirrel.ir import IR, Gate


def make_interaction_graph(ir: IR) -> nx.Graph:
    interaction_graph = nx.Graph()
    gates = (statement for statement in ir.statements if isinstance(statement, Gate))

    for gate in gates:
        target_qubits = gate.qubit_operands
        match len(target_qubits):
            case 1:
                continue

            case 2:
                interaction_graph.add_edge(*target_qubits)

            case _:
                msg = (
                    f"the gate {gate} acts on more than 2 qubits. ",
                    "The gate must be decomposed before an interaction graph can be made",
                )
                raise ValueError(msg)

    return interaction_graph
