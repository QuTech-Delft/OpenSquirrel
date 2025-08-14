All single-qubit gates appearing in a circuit can be merged by applying `merge(merger=SingleQubitGatesMerger())` to the circuit.
Note that multi-qubit gates remain untouched and single-qubit gates are not merged across any multi-qubit gates.
The gate that results from the merger of single-qubit gates will, in general,
comprise an arbitrary rotation and, therefore, not be a known gate.
In OpenSquirrel an unrecognized gate is deemed _anonymous_.
When a circuit contains anonymous gates and is written to a cQASM string,
the semantic representation of the anonymous gate is exported.

```python
from opensquirrel import CircuitBuilder
from opensquirrel.passes.merger import SingleQubitGatesMerger
import math

builder = CircuitBuilder(1)
for _ in range(4):
    builder.Rx(0, math.pi / 4)
circuit = builder.to_circuit()

circuit.merge(merger=SingleQubitGatesMerger())

print(circuit)
```

??? example "`print(circuit)`"

    version 3.0

    qubit[1] q

    Rx(pi) q[0]

In the above example, OpenSquirrel has merged all the Rx gates together.
