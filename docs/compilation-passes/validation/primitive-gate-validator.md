When developing quantum algorithms, their compilation on a specific device depends on whether the hardware supports the
operations implemented on the circuit.

To this end, the primitive gate validator pass checks whether the quantum gates in the
quantum circuit are present in the primitive gate set of the target backend.
If this is not the case, the validator will throw a `ValueError`,
specifying which gates in the circuit are not in the provided primitive gate set.

Below are some examples of using the primitive gate validator (`PrimitiveGateValidator`).

_Check the [circuit builder](../../circuit-builder/index.md) on how to generate a circuit._

```python
from opensquirrel import CircuitBuilder
from opensquirrel.passes.validator import PrimitiveGateValidator
```

```python
from math import pi
pgs = ["I", "Rx", "Ry", "Rz", "CZ"]

builder = CircuitBuilder(5)
builder.Rx(pi / 2)
builder.Ry(1, -pi / 2)
builder.CZ(0, 1)
builder.Ry(1, pi / 2)
circuit = builder.to_circuit()

circuit.validate(validator=PrimitiveGateValidator(primitive_gate_set=pgs))
```

In the scenario above, there will be no output, as all gates in the circuit are in the primitive gate set.
On the other hand, the circuit below will raise an error (`ValueError`) as certain gates are not supported,
given the backend primitive gate set (`pgs`).

```python
pgs = ["I", "X90", "mX90", "Y90", "mY90", "Rz", "CZ"]

builder = CircuitBuilder(5)
builder.I(0)
builder.X90(1)
builder.mX90(2)
builder.Y90(3)
builder.mY90(4)
builder.Rz(0, 2)
builder.CZ(1, 2)
builder.H(0)
builder.CNOT(1, 2)
circuit = builder.to_circuit()

circuit.validate(validator=PrimitiveGateValidator(primitive_gate_set=pgs))
```

!!! example ""

    `ValueError: the following gates are not in the primitive gate set: ['H', 'CNOT']`

!!! note "Resolving the error"

    The upsupported gates can be replaced manually, or a [decomposition pass](../decomposition/index.md) can be used to
    resolve the error.

