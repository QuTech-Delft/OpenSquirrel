Analyzer passe in OpenSquirrel is used to compute statistics that describe the structure of a quantum circuit.
Unlike most other passes, an analyzer does not modify the circuit: it inspects it and returns a set of metrics.
These metrics can be used, for instance, to characterise a circuit prior to compilation, to compare circuits, or as input features for machine-learning models that predict compilation performance.

OpenSquirrel currently facilitates the following analysis pass:

- [Circuit analyzer](circuit-analyzer.md) (`CircuitAnalyzer`)