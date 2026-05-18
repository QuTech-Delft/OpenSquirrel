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
# Size & Depth metrics                                                  #
# --------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("circuit_name", "exp_qubits", "exp_gates", "exp_2q", "exp_pct", "exp_depth"),
    [
        ("empty_circuit", 3, 0, 0, 0.0, 0),
        ("ghz_circuit", 3, 3, 2, 2 / 3, 3),
    ],
)
def test_size_metrics(
    analyzer: CircuitAnalyzer,
    request: pytest.FixtureRequest,
    circuit_name: str,
    exp_qubits: int,
    exp_gates: int,
    exp_2q: int,
    exp_pct: float,
    exp_depth: int,
) -> None:
    circuit = request.getfixturevalue(circuit_name)
    result = analyzer.analyze(circuit)

    assert result["n_qubits"] == exp_qubits
    assert result["n_gates"] == exp_gates
    assert result["n_two_qubit_gates"] == exp_2q
    assert result["two_qubit_pct"] == pytest.approx(exp_pct, abs=1e-3)
    assert result["depth"] == exp_depth


@pytest.mark.parametrize(
    ("circuit_name", "exp_depth", "exp_gates"),
    [
        ("parallel_circuit", 1, 2),
        ("sequential_circuit", 3, 3),
    ],
)
def test_depth_metrics(
    analyzer: CircuitAnalyzer, request: pytest.FixtureRequest, circuit_name: str, exp_depth: int, exp_gates: int
) -> None:
    circuit = request.getfixturevalue(circuit_name)
    result = analyzer.analyze(circuit)

    assert result["depth"] == exp_depth
    assert result["n_gates"] == exp_gates


# --------------------------------------------------------------------- #
# Interaction graph metrics                                             #
# --------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("circuit_name", "exp_diameter", "exp_avg_degree", "exp_cliques", "exp_clustering"),
    [
        ("single_qubit_circuit", 0, 0.0, 0, 0.0),
        ("ghz_circuit", 2, 4 / 3, 2, 0.0),
    ],
)
def test_interaction_graph_metrics(
    analyzer: CircuitAnalyzer,
    request: pytest.FixtureRequest,
    circuit_name: str,
    exp_diameter: int,
    exp_avg_degree: float,
    exp_cliques: int,
    exp_clustering: float,
) -> None:
    circuit = request.getfixturevalue(circuit_name)
    result = analyzer.analyze(circuit)

    assert result["ig_diameter"] == exp_diameter
    assert result["ig_avg_degree"] == pytest.approx(exp_avg_degree, abs=1e-3)
    assert result["ig_n_maximal_cliques"] == exp_cliques
    assert result["ig_clustering_coefficient"] == pytest.approx(exp_clustering, abs=1e-9)


# --------------------------------------------------------------------- #
# Gate dependency graph metrics                                         #
# --------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("circuit_name", "exp_cp_length", "exp_pct"),
    [
        ("sequential_circuit", 2, 1.0),
        ("parallel_circuit", 0, 1.0),
        ("empty_circuit", 0, 0.0),
    ],
)
def test_critical_path_metrics(
    analyzer: CircuitAnalyzer, request: pytest.FixtureRequest, circuit_name: str, exp_cp_length: int, exp_pct: float
) -> None:
    circuit = request.getfixturevalue(circuit_name)
    result = analyzer.analyze(circuit)

    assert result["gdg_critical_path_length"] == exp_cp_length
    assert result["gdg_pct_gates_in_critical_path"] == pytest.approx(exp_pct, abs=1e-9)


def test_gdg_path_length_stats_on_empty_circuit(analyzer: CircuitAnalyzer, empty_circuit: Circuit) -> None:
    """Ensure that standard deviation and mean don't throw errors on empty graphs."""
    result = analyzer.analyze(empty_circuit)
    assert result["gdg_path_length_mean"] == pytest.approx(0.0, abs=1e-9)
    assert result["gdg_path_length_std"] == pytest.approx(0.0, abs=1e-9)


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
