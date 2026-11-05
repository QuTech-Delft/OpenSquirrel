The two-qubit gates merger (`TwoQubitGatesMerger`) allows combining gates acting on the same pair of qubits into a single
two-qubit gate. Single-qubit gates on either qubit can be included in the sequence being merged.
This can reduce circuit depth, but the resulting gate may be an arbitrary two-qubit gate rather than a known gate.

Merging does not cross _non-unitary_ instructions, _e.g._ `init`, `reset`, and `measure`, or _control_ instructions,from
_e.g._ `wait` and `barrier`. Gates acting on other qubits are not included in the merged gate. OpenSquirrel will try to identify whether the resulting two-qubit gate is a _known_ gate.

To execute the resulting circuit on a backend with a limited primitive gate set, it may be necessary to apply a
[decomposition](../decomposition/index.md) pass. The [canonical to CZ decomposer](../decomposition/can2cz-decomposer.md)
(`Can2CZDecomposer`) can decompose arbitrary two-qubit gates into (at most three) CZ gates and single-qubit gates.

The example below shows how four CR gates acting on the same pair are merged into a single CZ gate.
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

??? example "`print(circuit)`"

    ```
    version 3.0

    qubit[2] q

    CZ q[0], q[1]
    ```

The example above show how four consecutive controlled Rz rotations over $\pi/4$, are merged into a single CZ gate.

The following example shows that single-qubit gates are also included in the merge.


```python
builder = CircuitBuilder(3)
builder.SWAP(0, 1).CZ(0, 1).S(0).S(1)
circuit = builder.to_circuit()

circuit.merge(merger=TwoQubitGatesMerger())
```

??? example "`print(circuit)`"

    ```
    version 3.0

    qubit[2] q

    ISWAP q[0], q[1]
    ```

Be aware that the merging happens in a _greedy_ manner, so a two-qubit gate will merge with as many single-qubit gates as possible, until a new two-qubit gate is encountered.

