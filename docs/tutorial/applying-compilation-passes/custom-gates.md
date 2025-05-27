OpenSquirrel accepts any new gate and requires its definition in terms of a semantic.
Creating new gates is done using Python functions, decorators, and one of the following gate semantic classes:
`BlochSphereRotation`, `ControlledGate`, or `MatrixGate`.

- The `BlochSphereRotation` class is used to define an arbitrary single qubit gate.
It accepts a qubit, an axis, an angle, and a phase as arguments.
Below is shown how the X-gate is defined in the default gate set of OpenSquirrel:

```python
from opensquirrel.ir import Gate, BlochSphereRotation, QubitLike, named_gate
import math

@named_gate
def x(q: QubitLike) -> Gate:
    return BlochSphereRotation(qubit=q, axis=(1, 0, 0), angle=math.pi, phase=math.pi / 2)
```

Notice the `@named_gate` decorator.
This _tells_ OpenSquirrel that the function defines a gate and that it should,
therefore, have all the nice properties OpenSquirrel expects of it.

- The `ControlledGate` class is used to define a multiple qubit gate that comprises a controlled operation.
For instance, the `CNOT` gate is defined in the default gate set of OpenSquirrel as follows:

```python
from opensquirrel.ir import Gate, ControlledGate, QubitLike, named_gate
from opensquirrel import X

@named_gate
def cnot(control: QubitLike, target: QubitLike) -> Gate:
    return ControlledGate(control, X(target))
```

- The `MatrixGate` class may be used to define a gate in the generic form of a matrix:

```python
from opensquirrel.ir import Gate, MatrixGate, QubitLike, named_gate

@named_gate
def swap(q1: QubitLike, q2: QubitLike) -> Gate:
    return MatrixGate(
        [
            [1, 0, 0, 0],
            [0, 0, 1, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1],
        ],
        [q1, q2],
    )
```

!!! note

    User defined gates can only be used in when creating a circuit with the circuit builder.
    [cQASM](https://qutech-delft.github.io/cQASM-spec) parsers will not recognize user defined gates, _i.e._,
    they cannot be used when creating a circuit through a cQASM string.