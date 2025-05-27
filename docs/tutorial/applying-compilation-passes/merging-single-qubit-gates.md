All single-qubit gates appearing in a circuit can be merged by applying `merge(merger=SingleQubitGatesMerger())` to the circuit.
Note that multi-qubit gates remain untouched and single-qubit gates are not merged across any multi-qubit gates.
The gate that results from the merger of single-qubit gates will, in general,
comprise an arbitrary rotation and, therefore, not be a known gate.
In OpenSquirrel an unrecognized gate is deemed _anonymous_.
When a circuit contains anonymous gates and is written to a cQASM string,
the semantic representation of the anonymous gate is exported.

!!! warning

    The semantic representation of an anonymous gate is not compliant
    [cQASM](https://qutech-delft.github.io/cQASM-spec), meaning that
    a cQASM parser, _e.g._ [libQASM](https://qutech-delft.github.io/libqasm/),
    will not recognize it as a valid statement.

```python
from opensquirrel.circuit_builder import CircuitBuilder
from opensquirrel.passes.merger import SingleQubitGatesMerger
from opensquirrel.ir import Float
import math

builder = CircuitBuilder(1)
for _ in range(4):
    builder.Rx(0, math.pi / 4)
qc = builder.to_circuit()

qc.merge(merger=SingleQubitGatesMerger())

print(qc)
```
_Output_:

    version 3.0

    qubit[1] q

    BlochSphereRotation(qubit=Qubit[0], axis=[1. 0. 0.], angle=3.14159, phase=0.0)

In the above example, OpenSquirrel has merged all the Rx gates together.
Yet, for now, OpenSquirrel does not recognize that this results in a single Rx
over the cumulated angle of the individual rotations.
Moreover, it does not recognize that the result corresponds to the X gate (up to a global phase difference).
At a later stage, we may want OpenSquirrel to recognize the resultant gate
in the case it is part of the set of known gates.

The gate set is, however, not immutable.
In the following section, we demonstrate how new gates can be defined and added to the default gate set.
