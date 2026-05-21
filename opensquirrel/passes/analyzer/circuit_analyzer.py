from __future__ import annotations

import math
import statistics
from typing import TYPE_CHECKING, Any

import networkx as nx

from opensquirrel.ir.two_qubit_gate import TwoQubitGate
from opensquirrel.ir.unitary import Gate
from opensquirrel.passes.analyzer.general_analyzer import Analyzer

if TYPE_CHECKING:
    from opensquirrel.circuit import Circuit


class CircuitAnalyzer(Analyzer):
    """Computes structural metrics describing a quantum circuit.

    The metrics are grouped into four categories:

    * Size: number of qubits, gates, two-qubit gates, two-qubit gate percentage, depth.
    * Interaction graph (IG): metrics derived from the qubit interaction graph,
      where nodes correspond to qubits and edges correspond to two-qubit gates.
    * Gate dependency graph (GDG): metrics derived from the directed acyclic graph
      of gate-to-gate dependencies on shared qubits.
    * Density: parallelisation-related metrics (density score, idling score).

    The metric set follows the structural circuit profiling approach proposed
    in Bandic et al., "Profiling quantum circuits for their efficient execution
    on single- and multi-core architectures" (Quantum Sci. Technol. 10, 015060, 2025).

    """

    def analyze(self, circuit: Circuit) -> dict[str, Any]:
        """Run the analyzer on the given circuit and return all metrics.

        Args:
            circuit (Circuit): The circuit to analyze.

        Returns:
            dict[str, Any]: A flat dictionary mapping metric name to its value.

        """
        self.circuit = circuit
        self.gate_statements = [s for s in circuit.ir.statements if isinstance(s, Gate)]

        metrics: dict[str, Any] = {}
        metrics.update(self._size_metrics())
        metrics.update(self._interaction_graph_metrics())
        metrics.update(self._gate_dependency_graph_metrics())
        metrics.update(self._density_metrics())

        return metrics

    # ------------------------------------------------------------------ #
    # Size metrics                                                       #
    # ------------------------------------------------------------------ #
    def _size_metrics(self) -> dict[str, Any]:
        n_qubits = self.circuit.qubit_register_size
        n_gates = len(self.gate_statements)
        n_two_qubit_gates = sum(1 for s in self.gate_statements if isinstance(s, TwoQubitGate))
        two_qubit_pct = round(n_two_qubit_gates / n_gates, 4) if n_gates > 0 else 0.0
        depth = self._compute_depth()

        return {
            "n_qubits": n_qubits,
            "n_gates": n_gates,
            "n_two_qubit_gates": n_two_qubit_gates,
            "two_qubit_pct": two_qubit_pct,
            "depth": depth,
        }

    def _compute_depth(self) -> int:
        """ASAP-style circuit depth (longest dependency chain)."""
        n_qubits = self.circuit.qubit_register_size
        if n_qubits == 0 or not self.gate_statements:
            return 0

        layer = [0] * n_qubits
        for gate_statement in self.gate_statements:
            qubit_indices = list(gate_statement.qubit_indices)
            new_layer = max(layer[qubit_index] for qubit_index in qubit_indices) + 1
            for qubit_index in qubit_indices:
                layer[qubit_index] = new_layer
        return max(layer)

    # ------------------------------------------------------------------ #
    # Interaction graph metrics                                          #
    # ------------------------------------------------------------------ #
    def _interaction_graph_metrics(self) -> dict[str, Any]:
        weighted_edges = self.circuit.interaction_graph
        if not weighted_edges:
            return {
                "ig_avg_shortest_path": 0.0,
                "ig_std_adjacency": 0.0,
                "ig_diameter": 0,
                "ig_central_dominance": 0.0,
                "ig_avg_degree": 0.0,
                "ig_n_maximal_cliques": 0,
                "ig_clustering_coefficient": 0.0,
            }

        graph = nx.Graph()
        graph.add_nodes_from(range(self.circuit.qubit_register_size))
        for (i, j), weight in weighted_edges.items():
            graph.add_edge(i, j, weight=weight)

        # avg_shortest_path: computed on the largest connected component.
        try:
            largest_cc_nodes = max(nx.connected_components(graph), key=len)
            largest_cc = graph.subgraph(largest_cc_nodes)
            avg_shortest_path = (
                round(nx.average_shortest_path_length(largest_cc), 4) if largest_cc.number_of_nodes() > 1 else 0.0
            )
        except (nx.NetworkXError, ValueError):
            avg_shortest_path = 0.0

        # std of adjacency matrix entries
        adjacency_matrix = nx.to_numpy_array(graph)
        std_adjacency = round(float(adjacency_matrix.std()), 4)

        # diameter: undefined for disconnected graphs so we use 0 in that case.
        try:
            diameter = nx.diameter(graph) if nx.is_connected(graph) else 0
        except nx.NetworkXError:
            diameter = 0

        # central point of dominance: max betweenness across nodes.
        betweenness = nx.betweenness_centrality(graph)
        central_dominance = round(max(betweenness.values()), 4) if betweenness else 0.0

        # average degree
        degrees = [d for _, d in graph.degree()]
        avg_degree = round(sum(degrees) / len(degrees), 4) if degrees else 0.0

        # number of maximal cliques
        try:
            n_maximal_cliques = sum(1 for _ in nx.find_cliques(graph))
        except nx.NetworkXError:
            n_maximal_cliques = 0

        # average clustering coefficient
        clustering_coefficient = round(nx.average_clustering(graph), 4)

        return {
            "ig_avg_shortest_path": avg_shortest_path,
            "ig_std_adjacency": std_adjacency,
            "ig_diameter": diameter,
            "ig_central_dominance": central_dominance,
            "ig_avg_degree": avg_degree,
            "ig_n_maximal_cliques": n_maximal_cliques,
            "ig_clustering_coefficient": clustering_coefficient,
        }

    # ------------------------------------------------------------------ #
    # Gate dependency graph metrics                                      #
    # ------------------------------------------------------------------ #
    def _gate_dependency_graph_metrics(self) -> dict[str, Any]:
        n_gates = len(self.gate_statements)
        if n_gates == 0:
            return {
                "gdg_critical_path_length": 0,
                "gdg_path_length_mean": 0.0,
                "gdg_path_length_std": 0.0,
                "gdg_pct_gates_in_critical_path": 0.0,
            }

        gate_dependency_graph = self._build_gate_dependency_graph()
        critical_path_length = self._safe_critical_path_length(gate_dependency_graph)
        longest_to, longest_from = self._compute_longest_paths(gate_dependency_graph)
        mean_length, std_length = self._path_length_stats(longest_to)
        pct_gates_in_cp = self._critical_path_membership_fraction(
            gate_dependency_graph, longest_to, longest_from, critical_path_length, n_gates
        )

        return {
            "gdg_critical_path_length": critical_path_length,
            "gdg_path_length_mean": round(mean_length, 4),
            "gdg_path_length_std": round(std_length, 4),
            "gdg_pct_gates_in_critical_path": pct_gates_in_cp,
        }

    def _build_gate_dependency_graph(self) -> nx.DiGraph:
        """Build a directed acyclic gate dependency graph where edge (i, j) means gate i must run before gate j."""
        gate_dependency_graph: nx.DiGraph = nx.DiGraph()
        last_gate_on_qubit: dict[int, int] = {}
        for index, gate in enumerate(self.gate_statements):
            gate_dependency_graph.add_node(index)
            for qubit_index in gate.qubit_indices:
                if qubit_index in last_gate_on_qubit:
                    gate_dependency_graph.add_edge(last_gate_on_qubit[qubit_index], index)
                last_gate_on_qubit[qubit_index] = index
        return gate_dependency_graph

    def _safe_critical_path_length(self, gate_dependency_graph: nx.DiGraph) -> int:
        try:
            return nx.dag_longest_path_length(gate_dependency_graph)
        except nx.NetworkXError:
            return 0

    def _compute_longest_paths(self, gate_dependency_graph: nx.DiGraph) -> tuple[dict[int, int], dict[int, int]]:
        """Return (longest_from, longest_to) for every node in the gate dependency graph.

        longest_to[n]   = length of the longest path ending at n
        longest_from[n] = length of the longest path starting at n
        """
        topo_order = list(nx.topological_sort(gate_dependency_graph))
        longest_to: dict[int, int] = dict.fromkeys(gate_dependency_graph.nodes, 0)
        for node in topo_order:
            for successor in gate_dependency_graph.successors(node):
                if longest_to[node] + 1 > longest_to[successor]:
                    longest_to[successor] = longest_to[node] + 1

        longest_from: dict[int, int] = dict.fromkeys(gate_dependency_graph.nodes, 0)
        for node in reversed(topo_order):
            for successor in gate_dependency_graph.successors(node):
                if longest_from[successor] + 1 > longest_from[node]:
                    longest_from[node] = longest_from[successor] + 1

        return longest_from, longest_to

    def _path_length_stats(self, longest_to: dict[int, int]) -> tuple[float, float]:
        path_lengths = list(longest_to.values())
        if not path_lengths:
            return 0.0, 0.0
        mean_length = statistics.mean(path_lengths)
        variance = statistics.pstdev(path_lengths)
        return mean_length, math.sqrt(variance)

    def _critical_path_membership_fraction(
        self,
        gate_dependency_graph: nx.DiGraph,
        longest_to: dict[int, int],
        longest_from: dict[int, int],
        critical_path_length: int,
        n_gates: int,
    ) -> float:
        """Fraction of gates that lie on some critical path.

        A node lies on a critical path iff the longest path through it
        (longest_to[n] + longest_from[n]) equals the overall critical path length.
        """
        n_in_cp = sum(
            1 for node in gate_dependency_graph.nodes if longest_to[node] + longest_from[node] == critical_path_length
        )
        return round(n_in_cp / n_gates, 4)

    # ------------------------------------------------------------------ #
    # Density metrics                                                    #
    # ------------------------------------------------------------------ #

    def _density_metrics(self) -> dict[str, Any]:
        n_qubits = self.circuit.qubit_register_size
        n_gates = len(self.gate_statements)
        n_two_qubit_gates = sum(1 for s in self.gate_statements if isinstance(s, TwoQubitGate))
        n_one_qubit_gates = n_gates - n_two_qubit_gates
        depth = self._compute_depth()

        # Density score: parallelisation level of the circuit (0..1).
        # Formula from Bandic et al. 2025, eq. (1).
        if n_qubits > 1 and depth > 1:
            density_score = (2 * n_two_qubit_gates + n_one_qubit_gates) / ((depth - 1) * (n_qubits - 1))
            density_score = round(min(density_score, 1.0), 4)
        else:
            density_score = 0.0

        # Idling score: average qubit idling fraction (0..1).
        if n_qubits > 0 and depth > 0:
            qubit_active_layers: dict[int, int] = dict.fromkeys(range(n_qubits), 0)
            for gate_statement in self.gate_statements:
                for qubit_index in gate_statement.qubit_indices:
                    qubit_active_layers[qubit_index] = qubit_active_layers.get(qubit_index, 0) + 1
            total_idle = sum(depth - active for active in qubit_active_layers.values())
            idling_score = round(max(0.0, min(total_idle / (n_qubits * depth), 1.0)), 4)
        else:
            idling_score = 0.0

        return {"density_score": density_score, "idling_score": idling_score}
