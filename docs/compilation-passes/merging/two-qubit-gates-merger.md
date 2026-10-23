The two-qubit gates merger (`TwoQubitGatesMerger`) allows combining gates acting on the same pair of qubits into a single
two-qubit gate. Single-qubit gates on either qubit can be included in the sequence being merged.
This can reduce circuit depth, but the resulting gate may be an arbitrary two-qubit gate rather than a known gate.

Merging does not cross _non-unitary_ instructions, _e.g._ `init`, `reset`, and `measure`, or _control_ instructions,from
_e.g._ `wait` and `barrier`. Gates acting on other qubits are not included in the merged gate. OpenSquirrel will not try to identify whether the resulting two-qubit gate is a _known_ gate.

To execute the resulting circuit on a backend with a limited primitive gate set, it may be necessary to apply a
[decomposition](../decomposition/index.md) pass. The [canonical to CZ decomposer](../decomposition/can2cz-decomposer.md)
(`Can2CZDecomposer`) can decompose arbitrary two-qubit gates into (at most three) CZ gates and single-qubit gates.

The example below shows how three CNOT gates acting on the same pair are merged into a single SWAP gate.
Note that the `TwoQubitGatesMerger` pass does not require any input arguments.

_Check the [circuit builder](../../circuit-builder/index.md) on how to generate a circuit._

```python
from opensquirrel import CircuitBuilder
from opensquirrel.passes.merger import TwoQubitGatesMerger
from math import pi  # not necessary for using the TwoQubitGatesMerger
```

```python
builder = CircuitBuilder(3)
for _ in range(4):
    builder.CR(0, 1, pi / 4)
circuit = builder.to_circuit()

circuit.merge(merger=TwoQubitGatesMerger())
```

The three CNOT gates are replaced by one `TwoQubitGate` whose matrix is equivalent to SWAP. The merger represents the
result as a general two-qubit unitary; it does not identify the matrix as a named gate. In general, the merged gate is
equivalent to the original sequence up to a global phase, and a decomposition pass may be needed before execution on a
particular backend.