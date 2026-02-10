The ABA decomposer is a collection of single-qubit gate decomposers that follow the A-B-A pattern,
where the A and B stand for a rotation gate about a particular axis (and A is not the same as B).
The following decomposers are available:

- XYX decomposer (`XYXDecomposer`)
- XZX decomposer (`XZXDecomposer`)
- YXY decomposer (`YXYDecomposer`)
- YZY decomposer (`YZYDecomposer`)
- ZXZ decomposer (`ZXZDecomposer`)
- ZYZ decomposer (`ZYZDecomposer`)

For instance, the ZYZ decomposer, decomposes every single-qubit gate into (at most) 3 gates,
 _i.e._, a sequence of an Rz, Ry, and Rz gate.
The decomposition is done in fewer than 3 gates where possible.

In the example below a H, Z, Y, and Rx gate are all decomposed to Rz and Ry gates using the ZYZ decomposer.

_Check the [circuit builder](../../circuit-builder/index.md) on how to generate a circuit._

```python
import math
from opensquirrel.circuit_builder import CircuitBuilder
from opensquirrel.passes.decomposer import ZYZDecomposer
```

```python
builder = CircuitBuilder(qubit_register_size=1)
builder.H(0).Z(0).Y(0).Rx(0, math.pi / 3)
circuit = builder.to_circuit()

circuit.decompose(decomposer=ZYZDecomposer())

```

??? example "`print(circuit)`"

    ```linenums="1"

    version 3.0

    qubit[1] q

    Rz(3.1415927) q[0]
    Ry(1.5707963) q[0]
    Rz(3.1415927) q[0]
    Ry(3.1415927) q[0]
    Rz(1.5707963) q[0]
    Ry(1.0471976) q[0]
    Rz(-1.5707963) q[0]

    ```
