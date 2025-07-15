This pass checks whether all interactions in the circuit, _i.e._ two-qubit gates, are executable given the backend
connectivity.
If certain interactions are not possible, the validator will throw a `ValueError`,
specifying which interactions cannot be executed.

The interaction validator (`InteractionValidator`) can be used in the following manner.

_Check the [circuit builder](../../circuit-builder/index.md) on how to generate a circuit._

```python
from opensquirrel import CircuitBuilder
from opensquirrel.passes.validator import InteractionValidator
```

```python
connectivity = {
    "0": [1, 2],
    "1": [0, 2, 3],
    "2": [0, 1, 4],
    "3": [1, 4],
    "4": [2, 3]
}

builder = CircuitBuilder(5)
builder.H(0)
builder.CNOT(0, 1)
builder.H(2)
builder.CNOT(1, 2)
builder.CNOT(2, 4)
builder.CNOT(3, 4)
circuit = builder.to_circuit()

interaction_validator = InteractionValidator(connectivity=connectivity)
circuit.validate(validator=interaction_validator)
```

In the scenario above, there will be no output since all qubit interactions are executable given the connectivity.
On the other hand, the circuit below will raise an error (`ValueError`) as certain interactions are not possible.

```python
builder = CircuitBuilder(5)
builder.H(0)
builder.CNOT(0, 1)
builder.CNOT(0, 3)
builder.H(2)
builder.CNOT(1, 2)
builder.CNOT(1, 3)
builder.CNOT(2, 3)
builder.CNOT(3, 4)
builder.CNOT(0, 4)
circuit = builder.to_circuit()

circuit.validate(validator=interaction_validator)
```

!!! example ""

    `ValueError: the following qubit interactions in the circuit prevent a 1-to-1 mapping:{(2, 3), (0, 3), (0, 4)}`

!!! note "Resolving the error"

    The circuit can be redefined to only contain interactions between connected qubits or a
    [routing pass](../routing/index.md) can be used to resolve the error.
