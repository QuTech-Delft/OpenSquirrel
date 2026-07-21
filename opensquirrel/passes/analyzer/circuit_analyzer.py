from __future__ import annotations

import math
import statistics
import warnings
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import TYPE_CHECKING, Any, ClassVar

import networkx as nx

from opensquirrel.ir.two_qubit_gate import TwoQubitGate
from opensquirrel.ir.unitary import Gate
from opensquirrel.passes.analyzer.general_analyzer import Analyzer

if TYPE_CHECKING:
    from collections.abc import Iterable

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

    Individual metrics can be (de)selected through the ``metrics`` and ``exclude_metrics``
    parameters, and a per-metric time-out can be set through the ``timeout`` parameter.
    The available metric names are returned by :meth:`available_metrics`.

    Args:
        metrics (Iterable[str] | None): Names of the metrics to compute.
            If None (default), all available metrics are computed.
        exclude_metrics (Iterable[str] | None): Names of the metrics to exclude
            from the computation. Applied after ``metrics``.
        timeout (float | None): Maximum time in seconds allowed for computing each
            individual metric. If a metric exceeds the time-out, its value is set to
            None and a UserWarning is emitted. If None (default), no time-out is applied.

    Raises:
        ValueError: If an unknown metric name is passed, or if ``timeout`` is not positive.

    """

    def __init__(
        self,
        metrics: Iterable[str] | None = None,
        exclude_metrics: Iterable[str] | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

        requested = set(self._METRIC_REGISTRY) if metrics is None else set(metrics)
        excluded = set(exclude_metrics) if exclude_metrics is not None else set()

        unknown = (requested | excluded) - set(self._METRIC_REGISTRY)
        if unknown:
            msg = f"unknown metric(s): {sorted(unknown)}; available metrics are: {list(self._METRIC_REGISTRY)}"
            raise ValueError(msg)

        if timeout is not None and timeout <= 0:
            msg = f"timeout must be a positive number of seconds, got {timeout}"
            raise ValueError(msg)

        self.metrics = [name for name in self._METRIC_REGISTRY if name in requested and name not in excluded]
        self.timeout = timeout

    @classmethod
    def available_metrics(cls) -> list[str]:
        """Return the names of all metrics this analyzer can compute.

        Returns:
            list[str]: The available metric names, in the order they are reported.

        """
        return list(cls._METRIC_REGISTRY)

    def analyze(self, circuit: Circuit) -> dict[str, Any]:
        """Run the analyzer on the given circuit and return the selected metrics.

        Args:
            circuit (Circuit): The circuit to analyze.

        Returns:
            dict[str, Any]: A flat dictionary mapping metric name to its value.

        """
        self.circuit = circuit
        self.gate_statements = [s for s in circuit.ir.statements if isinstance(s, Gate)]
        self._cache: dict[str, Any] = {}

        if self.timeout is None:
            return {name: self._METRIC_REGISTRY[name](self) for name in self.metrics}
        return self._analyze_with_timeout()

    def _analyze_with_timeout(self) -> dict[str, Any]:
        """Compute each selected metric in a worker thread, bounded by the configured time-out."""
        metrics: dict[str, Any] = {}
        executor = ThreadPoolExecutor(max_workers=1)
        try:
            for name in self.metrics:
                future = executor.submit(self._METRIC_REGISTRY[name], self)
                try:
                    metrics[name] = future.result(timeout=self.timeout)
                except FuturesTimeoutError:
                    metrics[name] = None
                    warnings.warn(
                        f"computation of metric '{name}' exceeded the time-out of {self.timeout} s; "
                        "its value is set to None",
                        UserWarning,
                        stacklevel=3,
                    )

                    executor.shutdown(wait=False, cancel_futures=True)
                    executor = ThreadPoolExecutor(max_workers=1)
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
        return metrics

    def _get_or_compute(self, key: str, factory: Callable[[], Any]) -> Any:
        """Return the cached value for key, computing and caching it on first use."""
        if key not in self._cache:
            self._cache[key] = factory()
        return self._cache[key]

    # ------------------------------------------------------------------ #
    # Size metrics                                                       #
    # ------------------------------------------------------------------ #
    def _metric_n_qubits(self) -> int:
        return self.circuit.qubit_register_size

    def _metric_n_gates(self) -> int:
        return len(self.gate_statements)

    def _metric_n_two_qubit_gates(self) -> int:
        return sum(1 for s in self.gate_statements if isinstance(s, TwoQubitGate))

    def _metric_two_qubit_pct(self) -> float:
        n_gates = len(self.gate_statements)
        if n_gates == 0:
            return 0.0
        return round(self._metric_n_two_qubit_gates() / n_gates, 4)

    def _metric_depth(self) -> int:
        return self._get_or_compute("depth", self._compute_depth)

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
    def _interaction_graph(self) -> nx.Graph:
        """The qubit interaction graph as a networkx Graph, cached per analysis."""
        return self._get_or_compute("interaction_graph", self._build_interaction_graph)

    def _build_interaction_graph(self) -> nx.Graph:
        graph = nx.Graph()
        graph.add_nodes_from(range(self.circuit.qubit_register_size))
        for (i, j), weight in self.circuit.interaction_graph.items():
            graph.add_edge(i, j, weight=weight)
        return graph

    def _metric_ig_avg_shortest_path(self) -> float:
        graph = self._interaction_graph()
        if graph.number_of_edges() == 0:
            return 0.0
        # Computed on the largest connected component.
        try:
            largest_cc_nodes = max(nx.connected_components(graph), key=len)
            largest_cc = graph.subgraph(largest_cc_nodes)
            if largest_cc.number_of_nodes() > 1:
                return round(nx.average_shortest_path_length(largest_cc), 4)
        except (nx.NetworkXError, ValueError):
            pass
        return 0.0

    def _metric_ig_std_adjacency(self) -> float:
        graph = self._interaction_graph()
        if graph.number_of_edges() == 0:
            return 0.0
        adjacency_matrix = nx.to_numpy_array(graph)
        return round(float(adjacency_matrix.std()), 4)

    def _metric_ig_diameter(self) -> int:
        graph = self._interaction_graph()
        if graph.number_of_edges() == 0:
            return 0
        # Diameter is undefined for disconnected graphs so I use 0 in that case.
        try:
            return nx.diameter(graph) if nx.is_connected(graph) else 0
        except nx.NetworkXError:
            return 0

    def _metric_ig_central_dominance(self) -> float:
        graph = self._interaction_graph()
        if graph.number_of_edges() == 0:
            return 0.0
        # Central point of dominance: max betweenness across nodes.
        betweenness = nx.betweenness_centrality(graph)
        return round(max(betweenness.values()), 4) if betweenness else 0.0

    def _metric_ig_avg_degree(self) -> float:
        graph = self._interaction_graph()
        if graph.number_of_edges() == 0:
            return 0.0
        degrees = [d for _, d in graph.degree()]
        return round(sum(degrees) / len(degrees), 4) if degrees else 0.0

    def _metric_ig_n_maximal_cliques(self) -> int:
        graph = self._interaction_graph()
        if graph.number_of_edges() == 0:
            return 0
        try:
            return sum(1 for _ in nx.find_cliques(graph))
        except nx.NetworkXError:
            return 0

    def _metric_ig_clustering_coefficient(self) -> float:
        graph = self._interaction_graph()
        if graph.number_of_edges() == 0:
            return 0.0
        return round(nx.average_clustering(graph), 4)

    # ------------------------------------------------------------------ #
    # Gate dependency graph metrics                                      #
    # ------------------------------------------------------------------ #
    def _gate_dependency_graph(self) -> nx.DiGraph:
        """The gate dependency graph as a networkx DiGraph, cached per analysis."""
        return self._get_or_compute("gate_dependency_graph", self._build_gate_dependency_graph)

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

    def _longest_paths(self) -> tuple[dict[int, int], dict[int, int]]:
        """The (longest_from, longest_to) maps of the gate dependency graph, cached per analysis."""
        return self._get_or_compute("longest_paths", lambda: self._compute_longest_paths(self._gate_dependency_graph()))

    def _metric_gdg_critical_path_length(self) -> int:
        if not self.gate_statements:
            return 0
        return self._safe_critical_path_length(self._gate_dependency_graph())

    def _metric_gdg_path_length_mean(self) -> float:
        if not self.gate_statements:
            return 0.0
        longest_from, _ = self._longest_paths()
        mean_length, _ = self._path_length_stats(longest_from)
        return round(mean_length, 4)

    def _metric_gdg_path_length_std(self) -> float:
        if not self.gate_statements:
            return 0.0
        longest_from, _ = self._longest_paths()
        _, std_length = self._path_length_stats(longest_from)
        return round(std_length, 4)

    def _metric_gdg_pct_gates_in_critical_path(self) -> float:
        n_gates = len(self.gate_statements)
        if n_gates == 0:
            return 0.0
        gate_dependency_graph = self._gate_dependency_graph()
        critical_path_length = self._safe_critical_path_length(gate_dependency_graph)
        longest_from, longest_to = self._longest_paths()
        return self._critical_path_membership_fraction(
            gate_dependency_graph, longest_to, longest_from, critical_path_length, n_gates
        )

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

    def _path_length_stats(self, path_length_by_node: dict[int, int]) -> tuple[float, float]:
        path_lengths = list(path_length_by_node.values())
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
    def _metric_density_score(self) -> float:
        """Density score: parallelisation level of the circuit (0..1)."""
        n_qubits = self.circuit.qubit_register_size
        n_gates = len(self.gate_statements)
        n_two_qubit_gates = self._metric_n_two_qubit_gates()
        n_one_qubit_gates = n_gates - n_two_qubit_gates
        depth = self._metric_depth()

        if n_qubits > 1 and depth > 1:
            density_score = (2 * n_two_qubit_gates + n_one_qubit_gates) / ((depth - 1) * (n_qubits - 1))
            return round(min(density_score, 1.0), 4)
        return 0.0

    def _metric_idling_score(self) -> float:
        """Idling score: average qubit idling fraction (0..1)."""
        n_qubits = self.circuit.qubit_register_size
        depth = self._metric_depth()

        if n_qubits > 0 and depth > 0:
            qubit_active_layers: dict[int, int] = dict.fromkeys(range(n_qubits), 0)
            for gate_statement in self.gate_statements:
                for qubit_index in gate_statement.qubit_indices:
                    qubit_active_layers[qubit_index] = qubit_active_layers.get(qubit_index, 0) + 1
            total_idle = sum(depth - active for active in qubit_active_layers.values())
            return round(max(0.0, min(total_idle / (n_qubits * depth), 1.0)), 4)
        return 0.0

    # ------------------------------------------------------------------ #
    # Metric registry                                                    #
    # ------------------------------------------------------------------ #
    _METRIC_REGISTRY: ClassVar[dict[str, Callable[[CircuitAnalyzer], Any]]] = {
        # Size
        "n_qubits": _metric_n_qubits,
        "n_gates": _metric_n_gates,
        "n_two_qubit_gates": _metric_n_two_qubit_gates,
        "two_qubit_pct": _metric_two_qubit_pct,
        "depth": _metric_depth,
        # Interaction graph
        "ig_avg_shortest_path": _metric_ig_avg_shortest_path,
        "ig_std_adjacency": _metric_ig_std_adjacency,
        "ig_diameter": _metric_ig_diameter,
        "ig_central_dominance": _metric_ig_central_dominance,
        "ig_avg_degree": _metric_ig_avg_degree,
        "ig_n_maximal_cliques": _metric_ig_n_maximal_cliques,
        "ig_clustering_coefficient": _metric_ig_clustering_coefficient,
        # Gate dependency graph
        "gdg_critical_path_length": _metric_gdg_critical_path_length,
        "gdg_path_length_mean": _metric_gdg_path_length_mean,
        "gdg_path_length_std": _metric_gdg_path_length_std,
        "gdg_pct_gates_in_critical_path": _metric_gdg_pct_gates_in_critical_path,
        # Density
        "density_score": _metric_density_score,
        "idling_score": _metric_idling_score,
    }
