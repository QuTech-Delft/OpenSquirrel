The following example shows how to build a quantum circuit from a `cQASM` string.

```python
from opensquirrel import Circuit

circuit = Circuit.from_string(
    """
    version 3.0

    // Initialise a circuit with two qubits and a bit
    qubit[2] q
    bit[2] b

    // Create a Bell pair
    H q[0]
    CNOT q[0], q[1]

    // Measure qubits
    b = measure q
    """
)

print(circuit)
```
_Output_:

    version 3.0

    qubit[2] q
    bit[2] b

    H q[0]
    CNOT q[0], q[1]
    b[0] = measure q[0]
    b[1] = measure q[1]


For a more detailed overview, the `cQASM` documentation can be found by following [this link](https://qutech-delft.github.io/cQASM-spec).
