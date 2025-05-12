OpenSquirrel's entrypoint is the `Circuit` object, which represents a quantum circuit.
You can create a circuit in two different ways:

1. From a [cQASM string](../creating-a-circuit/from-a-cqasm-string.md)
2. By using the [`CircuitBuilder`](../creating-a-circuit/using-the-circuit-builder.md) in Python.

The _cQASM_ documentation can be found by clicking on [this link](https://qutech-delft.github.io/cQASM-spec).


When building quantum circuits, it is important to keep in mind that the quantum gates defined in _OpenSquirrel_ are
subject to [strong typing](../creating-a-circuit/strong-types.md) requirements.
