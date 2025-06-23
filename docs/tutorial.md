

## Creating a circuit

OpenSquirrel's entrypoint is the `Circuit`, which represents a quantum circuit.
You can create a circuit in two different ways:

 1. form a string written in [cQASM](https://qutech-delft.github.io/cQASM-spec), or;
 2. by using the `CircuitBuilder` in Python.

### 1. From a cQASM string

```python
from opensquirrel import Circuit

qc = Circuit.from_string(
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

print(qc)
```
_Output_:

    version 3.0

    qubit[2] q
    bit[2] b

    H q[0]
    CNOT q[0], q[1]
    b[0] = measure q[0]
    b[1] = measure q[1]


### 2. Using the `CircuitBuilder`

For creation of a circuit through Python, the `CircuitBuilder` can be used accordingly:

```python
from opensquirrel.circuit_builder import CircuitBuilder

builder = CircuitBuilder(qubit_register_size=2)
builder.Ry(0, 0.23).CNOT(0, 1)
qc = builder.to_circuit()

print(qc)
```
_Output_:

    version 3.0

    qubit[2] q

    Ry(0.23) q[0]
    CNOT q[0], q[1]

You can naturally use the functionalities available in Python to create your circuit:

```python
from opensquirrel.circuit_builder import CircuitBuilder

builder = CircuitBuilder(qubit_register_size=10)
for i in range(0, 10, 2):
    builder.H(i)
qc = builder.to_circuit()

print(qc)
```
_Output_:

    version 3.0

    qubit[10] q

    H q[0]
    H q[2]
    H q[4]
    H q[6]
    H q[8]

For instance, you can generate a quantum fourier transform (QFT) circuit as follows:

```python
from opensquirrel.circuit_builder import CircuitBuilder

qubit_register_size = 5
builder = CircuitBuilder(qubit_register_size)
for i in range(qubit_register_size):
      builder.H(i)
      for c in range(i + 1, qubit_register_size):
            builder.CRk(c, i, c-i+1)
qft = builder.to_circuit()

print(qft)
```
_Output_:

    version 3.0

    qubit[5] q

    H q[0]
    CRk(2) q[1], q[0]
    CRk(3) q[2], q[0]
    CRk(4) q[3], q[0]
    CRk(5) q[4], q[0]
    H q[1]
    CRk(2) q[2], q[1]
    CRk(3) q[3], q[1]
    CRk(4) q[4], q[1]
    H q[2]
    CRk(2) q[3], q[2]
    CRk(3) q[4], q[2]
    H q[3]
    CRk(2) q[4], q[3]
    H q[4]

### Strong types

As you can see, gates require _strong types_. For instance, you cannot do:

```python
from opensquirrel.circuit import Circuit

try:
    Circuit.from_string(
        """
        version 3.0
        qubit[2] q

        CNOT q[0], 3 // The CNOT expects a qubit as second argument.
        """
    )
except Exception as e:
    print(e)
```
_Output_:

    Parsing error: failed to resolve overload for cnot with argument pack (qubit, int)

The issue is that the `CNOT` expects a qubit as second input argument where an integer has been provided.




