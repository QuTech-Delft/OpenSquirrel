One of the most common single qubit decomposition techniques is the ZYZ decomposition.
This technique decomposes a quantum gate into an `Rz`, `Ry` and `Rz` gate in that order.
The decompositions are found in `opensquirrel.passes.decomposer`,
an example can be seen below where a `H`, `Z`, `Y`, and `Rx` gate are all decomposed on a single qubit circuit.

```python
from opensquirrel.circuit_builder import CircuitBuilder
from opensquirrel.passes.decomposer import ZYZDecomposer
import math

builder = CircuitBuilder(qubit_register_size=1)
builder.H(0).Z(0).Y(0).Rx(0, math.pi / 3)
circuit = builder.to_circuit()

circuit.decompose(decomposer=ZYZDecomposer())

print(circuit)
```
_Output_:

    version 3.0

    qubit[1] q

    Rz(3.1415927) q[0]
    Ry(1.5707963) q[0]
    Rz(3.1415927) q[0]
    Ry(3.1415927) q[0]
    Rz(1.5707963) q[0]
    Ry(1.0471976) q[0]
    Rz(-1.5707963) q[0]

Similarly, the decomposer can be used on individual gates.

```python
from opensquirrel.passes.decomposer import ZYZDecomposer
from opensquirrel import H

print(ZYZDecomposer().decompose(H(0)))
```
