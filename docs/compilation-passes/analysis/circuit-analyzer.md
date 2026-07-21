This pass computes a collection of structural metrics that describe a quantum circuit.
The metrics follow the circuit profiling approach proposed by Bandić _et al._[^1] and are grouped into four categories:

- **Size**: number of qubits, number of gates, number of two-qubit gates, two-qubit gate percentage, and circuit depth.
- **Interaction graph (IG)**: metrics derived from the qubit interaction graph, where nodes are qubits and edges are two-qubit gates (_e.g._, diameter, average degree, clustering coefficient).
- **Gate dependency graph (GDG)**: metrics derived from the directed acyclic graph of gate-to-gate dependencies on shared qubits (_e.g._, critical path length).
- **Density**: parallelisation-related metrics (density score and idling score).

The analysis returns a flat dictionary mapping each metric name to its value.
The circuit analyzer (`CircuitAnalyzer`) can be used in the following manner.

_Check the [circuit builder](../../circuit-builder/index.md) on how to generate a circuit._

```python
from opensquirrel import CircuitBuilder
from opensquirrel.passes.analyzer import CircuitAnalyzer
```

```python
builder = CircuitBuilder(3)
builder.H(0)
builder.CNOT(0, 1)
builder.CNOT(1, 2)
circuit = builder.to_circuit()

circuit_analyzer = CircuitAnalyzer()
metrics = circuit.analyze(analyzer=circuit_analyzer)
```

The `metrics` dictionary then contains the value of every metric:

!!! example ""

    ```python
    {
        "n_qubits": 3, "n_gates": 3, "n_two_qubit_gates": 2, "two_qubit_pct": 0.6667, "depth": 3,
        "ig_avg_shortest_path": 1.3333, "ig_std_adjacency": 0.4969, "ig_diameter": 2,
        "ig_central_dominance": 1.0, "ig_avg_degree": 1.3333, "ig_n_maximal_cliques": 2,
        "ig_clustering_coefficient": 0.0,
        "gdg_critical_path_length": 2, "gdg_path_length_mean": 1.0, "gdg_path_length_std": 0.9036,
        "gdg_pct_gates_in_critical_path": 1.0,
        "density_score": 1.0, "idling_score": 0.4444,
    }
    ```

## Selecting metrics

Some metrics can be expensive to compute on large circuits.
For instance, determining the average shortest path in the interaction graph can be costly.
To avoid computing metrics that are not needed, the analyzer accepts two parameters:

- `metrics`: an iterable of metric names to compute. When omitted, all metrics are computed.
- `exclude_metrics`: an iterable of metric names to leave out. It is applied after `metrics`.

The full list of metric names can be obtained through the `available_metrics` class method.

```python
CircuitAnalyzer.available_metrics()
```

To compute only a subset of the metrics, pass their names through the `metrics` parameter:

```python
circuit_analyzer = CircuitAnalyzer(metrics=["n_qubits", "n_gates", "depth"])
metrics = circuit.analyze(analyzer=circuit_analyzer)
```

!!! example ""

    ```python
    {"n_qubits": 3, "n_gates": 3, "depth": 3}
    ```

Alternatively, to compute every metric except a costly one, use `exclude_metrics`:

```python
circuit_analyzer = CircuitAnalyzer(exclude_metrics=["ig_avg_shortest_path"])
metrics = circuit.analyze(analyzer=circuit_analyzer)
```

The returned dictionary contains all metrics except `ig_avg_shortest_path`.
Regardless of the order in which metrics are requested, they are always reported in the canonical order given by
`available_metrics`.

!!! note "Unknown metric names"

    Passing a metric name that does not exist to either `metrics` or `exclude_metrics` raises a `ValueError`
    listing the available metric names.

## Setting a time-out

A per-metric time-out (in seconds) can be set through the `timeout` parameter.
Each metric is computed under this time budget; if a metric exceeds it, its value is set to `None`, a `UserWarning`
is emitted, and the analysis continues with the remaining metrics.

```python
circuit_analyzer = CircuitAnalyzer(timeout=5.0)
metrics = circuit.analyze(analyzer=circuit_analyzer)
```

In the example above, any metric that takes longer than five seconds to compute is reported as `None`.
The `timeout` parameter can be combined with `metrics` and `exclude_metrics`.

!!! note "Interrupting a computation"

    The time-out bounds how long the analyzer _waits_ for a metric.
    The underlying computation runs in a separate thread and cannot be forcibly interrupted,
    so it may continue in the background until it completes on its own.
    A positive value is required for `timeout`; a non-positive value raises a `ValueError`.

[^1]:
    M. Bandić _et al._, "Profiling quantum circuits for their efficient execution on single- and multi-core
    architectures", _Quantum Sci. Technol._ **10**, 015060 (2025).