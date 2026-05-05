# Tests for CircuitAnalyzer pass

import pytest

from opensquirrel import CircuitBuilder
from opensquirrel.circuit import Circuit
from opensquirrel.passes.analyzer import CircuitAnalyzer


@pytest.fixture
def analyzer() -> CircuitAnalyzer:
    return CircuitAnalyzer()


# --------------------------------------------------------------------- #
# Sample circuits                                                       #
# --------------------------------------------------------------------- #
@pytest.fixture
def empty_circuit() -> Circuit:
    """A circuit with qubits but no gates."""
    builder = CircuitBuilder(3)
    return builder.to_circuit()


@pytest.fixture
def single_qubit_circuit() -> Circuit:
    """A 1-qubit circuit with only single-qubit gates."""
    builder = CircuitBuilder(1)
    builder.H(0)
    builder.X(0)
    builder.H(0)
    return builder.to_circuit()


@pytest.fixture
def ghz_circuit() -> Circuit:
    """A linear 3-qubit GHZ-like circuit. 3 gates, depth 3, IG is a path graph."""
    builder = CircuitBuilder(3)
    builder.H(0)
    builder.CNOT(0, 1)
    builder.CNOT(1, 2)
    return builder.to_circuit()


@pytest.fixture
def parallel_circuit() -> Circuit:
    """4 qubits with two independent CNOTs."""
    builder = CircuitBuilder(4)
    builder.CNOT(0, 1)
    builder.CNOT(2, 3)
    return builder.to_circuit()


@pytest.fixture
def sequential_circuit() -> Circuit:
    """4 qubits, fully sequential CNOTs across them — depth 3, fully on critical path."""
    builder = CircuitBuilder(4)
    builder.CNOT(0, 1)
    builder.CNOT(1, 2)
    builder.CNOT(2, 3)
    return builder.to_circuit()


# --------------------------------------------------------------------- #
# Smoke / shape                                                         #
# --------------------------------------------------------------------- #
def test_returns_dict_with_expected_keys(analyzer: CircuitAnalyzer, ghz_circuit: Circuit) -> None:
    result = analyzer.analyze(ghz_circuit)

    expected_keys = {
        # Size
        "n_qubits",
        "n_gates",
        "n_two_qubit_gates",
        "two_qubit_pct",
        "depth",
        # Interaction graph
        "ig_avg_shortest_path",
        "ig_std_adjacency",
        "ig_diameter",
        "ig_central_dominance",
        "ig_avg_degree",
        "ig_n_maximal_cliques",
        "ig_clustering_coefficient",
        # Gate dependency graph
        "gdg_critical_path_length",
        "gdg_path_length_mean",
        "gdg_path_length_std",
        "gdg_pct_gates_in_critical_path",
        # Density
        "density_score",
        "idling_score",
    }
    assert set(result.keys()) == expected_keys


def test_circuit_analyze_method_returns_dict(ghz_circuit: Circuit) -> None:
    """The Circuit.analyze() method should propagate the analyzer's dict output."""
    result = ghz_circuit.analyze(analyzer=CircuitAnalyzer())
    assert isinstance(result, dict)
    assert result["n_qubits"] == 3


# --------------------------------------------------------------------- #
# Size metrics                                                          #
# --------------------------------------------------------------------- #
def test_size_metrics_on_empty_circuit(analyzer: CircuitAnalyzer, empty_circuit: Circuit) -> None:
    result = analyzer.analyze(empty_circuit)
    assert result["n_qubits"] == 3
    assert result["n_gates"] == 0
    assert result["n_two_qubit_gates"] == 0
    assert result["two_qubit_pct"] == pytest.approx(0.0, abs=1e-9)
    assert result["depth"] == 0


def test_size_metrics_on_ghz(analyzer: CircuitAnalyzer, ghz_circuit: Circuit) -> None:
    result = analyzer.analyze(ghz_circuit)
    assert result["n_qubits"] == 3
    assert result["n_gates"] == 3
    assert result["n_two_qubit_gates"] == 2
    assert result["two_qubit_pct"] == pytest.approx(2 / 3, abs=1e-3)
    assert result["depth"] == 3


def test_depth_with_parallel_gates(analyzer: CircuitAnalyzer, parallel_circuit: Circuit) -> None:
    """Two independent gates can run in the same time-step, so depth is 1."""
    result = analyzer.analyze(parallel_circuit)
    assert result["depth"] == 1
    assert result["n_gates"] == 2


def test_depth_with_sequential_gates(analyzer: CircuitAnalyzer, sequential_circuit: Circuit) -> None:
    """Gates that share qubits must serialise, so depth equals gate count."""
    result = analyzer.analyze(sequential_circuit)
    assert result["depth"] == 3
    assert result["n_gates"] == 3


# --------------------------------------------------------------------- #
# Interaction graph metrics                                             #
# --------------------------------------------------------------------- #
def test_interaction_graph_empty_when_no_two_qubit_gates(
    analyzer: CircuitAnalyzer, single_qubit_circuit: Circuit
) -> None:
    result = analyzer.analyze(single_qubit_circuit)
    assert result["ig_diameter"] == 0
    assert result["ig_avg_degree"] == pytest.approx(0.0, abs=1e-9)
    assert result["ig_n_maximal_cliques"] == 0
    assert result["ig_clustering_coefficient"] == pytest.approx(0.0, abs=1e-9)


def test_interaction_graph_metrics_on_ghz(analyzer: CircuitAnalyzer, ghz_circuit: Circuit) -> None:
    """GHZ-like has IG = path q0-q1-q2: 3 nodes, 2 edges, diameter 2."""
    result = analyzer.analyze(ghz_circuit)
    assert result["ig_diameter"] == 2
    # avg degree of a 3-node path = (1 + 2 + 1) / 3 ~= 1.333
    assert result["ig_avg_degree"] == pytest.approx(4 / 3, abs=1e-3)
    # 2 maximal cliques (each edge is a maximal clique)
    assert result["ig_n_maximal_cliques"] == 2


# --------------------------------------------------------------------- #
# Gate dependency graph metrics                                         #
# --------------------------------------------------------------------- #
def test_critical_path_on_sequential_circuit(analyzer: CircuitAnalyzer, sequential_circuit: Circuit) -> None:
    """Three sequential CNOTs form a chain. Critical path length = 2 (3 nodes, 2 edges)."""
    result = analyzer.analyze(sequential_circuit)
    assert result["gdg_critical_path_length"] == 2
    # All 3 gates lie on the unique critical path.
    assert result["gdg_pct_gates_in_critical_path"] == pytest.approx(1.0, abs=1e-9)


def test_critical_path_on_parallel_circuit(analyzer: CircuitAnalyzer, parallel_circuit: Circuit) -> None:
    """Two independent gates means no edges in the GDG, so critical path length is 0."""
    result = analyzer.analyze(parallel_circuit)
    assert result["gdg_critical_path_length"] == 0


def test_critical_path_empty_on_empty_circuit(analyzer: CircuitAnalyzer, empty_circuit: Circuit) -> None:
    result = analyzer.analyze(empty_circuit)
    assert result["gdg_critical_path_length"] == 0
    assert result["gdg_path_length_mean"] == pytest.approx(0.0, abs=1e-9)
    assert result["gdg_path_length_std"] == pytest.approx(0.0, abs=1e-9)
    assert result["gdg_pct_gates_in_critical_path"] == pytest.approx(0.0, abs=1e-9)


# --------------------------------------------------------------------- #
# Density metrics                                                       #
# --------------------------------------------------------------------- #
def test_density_metrics_in_unit_range(analyzer: CircuitAnalyzer, ghz_circuit: Circuit) -> None:
    result = analyzer.analyze(ghz_circuit)
    assert 0.0 <= result["density_score"] <= 1.0
    assert 0.0 <= result["idling_score"] <= 1.0


def test_density_zero_on_empty_circuit(analyzer: CircuitAnalyzer, empty_circuit: Circuit) -> None:
    result = analyzer.analyze(empty_circuit)
    assert result["density_score"] == pytest.approx(0.0, abs=1e-9)
    assert result["idling_score"] == pytest.approx(0.0, abs=1e-9)


def test_idling_score_high_when_one_qubit_unused() -> None:
    """If one qubit is never touched, idling score should reflect that.

    With a 2-qubit circuit, depth 2, qubit 0 fully active and qubit 1 fully idle:
    idling = ((depth - q0_active) + (depth - q1_active)) / (n_qubits * depth)
           = ((2 - 2) + (2 - 0)) / (2 * 2) = 0.5
    """
    builder = CircuitBuilder(2)
    builder.H(0)
    builder.X(0)
    circuit = builder.to_circuit()
    result = CircuitAnalyzer().analyze(circuit)
    assert result["idling_score"] == pytest.approx(0.5, abs=1e-3)
