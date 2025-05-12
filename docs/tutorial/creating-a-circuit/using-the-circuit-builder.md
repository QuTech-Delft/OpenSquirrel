Quantum circuits can also be defined using Python functionalities, via the `CircuitBuilder`, as shown below.

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

There are multiple types of gates that can be applied to the circuit, using the `CircuitBuilder`. These include:

- [Unitary Gates](../../circuit-builder/instructions/gates.md)
- [Non-Unitary Gates](../../circuit-builder/instructions/non-unitaries.md)
- [Control Gates](../../circuit-builder/instructions/control-instructions.md)
