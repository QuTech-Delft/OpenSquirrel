# Tests for CircuitAnalyzer pass

import pytest

from opensquirrel import Circuit, CircuitBuilder
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


# --------------------------------------------------------------------- #
# Metric (de)selection                                                  #
# --------------------------------------------------------------------- #
def test_available_metrics_matches_default_analysis_keys(ghz_circuit: Circuit) -> None:
    result = CircuitAnalyzer().analyze(ghz_circuit)
    assert list(result.keys()) == CircuitAnalyzer.available_metrics()


def test_select_subset_of_metrics(ghz_circuit: Circuit) -> None:
    selected_analyzer = CircuitAnalyzer(metrics=["n_qubits", "depth", "density_score"])
    result = selected_analyzer.analyze(ghz_circuit)
    assert set(result.keys()) == {"n_qubits", "depth", "density_score"}


def test_selected_metric_values_match_full_analysis(ghz_circuit: Circuit) -> None:
    full_result = CircuitAnalyzer().analyze(ghz_circuit)
    subset_result = CircuitAnalyzer(metrics=["ig_diameter", "gdg_critical_path_length"]).analyze(ghz_circuit)
    assert subset_result["ig_diameter"] == full_result["ig_diameter"]
    assert subset_result["gdg_critical_path_length"] == full_result["gdg_critical_path_length"]


def test_exclude_metrics(ghz_circuit: Circuit) -> None:
    excluding_analyzer = CircuitAnalyzer(exclude_metrics=["ig_avg_shortest_path", "ig_central_dominance"])
    result = excluding_analyzer.analyze(ghz_circuit)
    expected_keys = set(CircuitAnalyzer.available_metrics()) - {"ig_avg_shortest_path", "ig_central_dominance"}
    assert set(result.keys()) == expected_keys


def test_select_and_exclude_metrics_combined(ghz_circuit: Circuit) -> None:
    analyzer = CircuitAnalyzer(metrics=["n_qubits", "n_gates", "depth"], exclude_metrics=["depth"])
    result = analyzer.analyze(ghz_circuit)
    assert set(result.keys()) == {"n_qubits", "n_gates"}


def test_metric_order_is_canonical_regardless_of_selection_order(ghz_circuit: Circuit) -> None:
    analyzer = CircuitAnalyzer(metrics=["depth", "n_qubits"])
    result = analyzer.analyze(ghz_circuit)
    assert list(result.keys()) == ["n_qubits", "depth"]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"metrics": ["n_qubits", "not_a_metric"]},
        {"exclude_metrics": ["also_not_a_metric"]},
    ],
)
def test_unknown_metric_name_raises(kwargs: dict) -> None:
    with pytest.raises(ValueError, match="unknown metric"):
        CircuitAnalyzer(**kwargs)


# --------------------------------------------------------------------- #
# Time-out                                                              #
# --------------------------------------------------------------------- #
@pytest.mark.parametrize("timeout", [0, -1.5])
def test_non_positive_timeout_raises(timeout: float) -> None:
    with pytest.raises(ValueError, match="timeout must be a positive number"):
        CircuitAnalyzer(timeout=timeout)


def test_analysis_succeeds_within_timeout(ghz_circuit: Circuit) -> None:
    result = CircuitAnalyzer(timeout=60.0).analyze(ghz_circuit)
    assert result["n_qubits"] == 3
    assert None not in result.values()


def test_timed_out_metric_is_none_and_warns(ghz_circuit: Circuit, monkeypatch: pytest.MonkeyPatch) -> None:
    import time

    def slow_metric(self: CircuitAnalyzer) -> int:
        time.sleep(2.0)
        return 42

    monkeypatch.setitem(CircuitAnalyzer._METRIC_REGISTRY, "depth", slow_metric)
    analyzer = CircuitAnalyzer(metrics=["n_qubits", "depth", "n_gates"], timeout=0.1)

    with pytest.warns(UserWarning, match="exceeded the time-out"):
        result = analyzer.analyze(ghz_circuit)

    assert result["depth"] is None
    assert result["n_qubits"] == 3
    assert result["n_gates"] == 3
