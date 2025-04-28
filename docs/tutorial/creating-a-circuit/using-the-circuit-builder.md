# Building a quantum circuit with the _CircuitBuilder_

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

## Quantum Gates

There are various instructions (quantum gates) that can be applied to your circuit, using the `CircuitBuilder`.

### [Unitary Instructions](https://qutech-delft.github.io/cQASM-spec/latest/language_specification/statements/instructions/unitary_instructions.html)

| Name       | Operator       | Description                                      | Example                                                                 |
|------------|----------------|--------------------------------------------------|-------------------------------------------------------------------------|
| I          |     _I_        |               Identity gate                      | `builder.I(0)`                                                          |
| H          |     _H_        |               Hadamard gate                      | `builder.H(0)`                                                          |
| X          |     _X_        |                  Pauli-X                         | `builder.X(0)`                                                          |
| X90        | _X<sub>90</sub>_| Rotation around the x-axis of $\frac{\pi}{2}$   | `builder.X90(0)`                                                        |
| mX90       | _X<sub>-90</sub>_| Rotation around the x-axis of $\frac{-\pi}{2}$ | `builder.mX90(0)`                                                       |
| Y          |     _Y_        |                  Pauli-Y                         | `builder.Y(0)`                                                          |
| Y90        | _Y<sub>90</sub>_|  Rotation around the y-axis of $\frac{\pi}{2}$  | `builder.Y90(0)`                                                        |
| mY90       | _Y<sub>-90</sub>_| Rotation around the y-axis of $\frac{-\pi}{2}$ | `builder.mY90(0)`                                                       |
| Z          |     _Z_        |                  Pauli-Z                         | `builder.Z(0)`                                                          |
| S          |     _S_        |                 Phase gate                       | `builder.S(0)`                                                          |
| Sdag       | _S<sup>†</sup>_|                S dagger gate                     | `builder.Sdag(0)`                                                       |
| T          |     _T_        |                     T                            | `builder.T(0)`                                                          |
| Tdag       | _T<sup>†</sup>_|                T dagger gate                     | `builder.Tdag(0)`                                                       |
| Rx         | _R<sub>x</sub>($\theta$)_| Arbitrary rotation around x-axis       | `builder.Rx(0, 0.23)`                                                   |
| Ry         |  _R<sub>y</sub>($\theta$)_| Arbitrary rotation around y-axis      | `builder.Ry(0, 0.23)`                                                   |
| Rz         | _R<sub>z</sub>($\theta$)_    | 	Arbitrary rotation around z-axis | `builder.Rz(0, 2)`                                                      |
| Rn         | _R<sub>n</sub>(n<sub>x</sub>, n<sub>y</sub>, n<sub>z</sub>, $\theta$, $\phi$<sub>g</sub>)_ | Arbitrary rotation around specified axis  | `builder.Rn(0)`   |
| CZ         | _CZ_           |            Controlled-Z, Controlled-Phase        | `builder.CZ(1, 2)`                                                      |
| CR         | _CR(\theta)_   |    Controlled phase shift (arbitrary angle)      | `builder.CR(0, 1, math.pi)`                                             |
| CRk        |  _CR<sub>k</sub>(k)_   | Controlled phase shift ($\frac{\pi}{2^{k-1}}$)             | `builder.CRk(1, 0, 2)`                                |
| SWAP       |    _SWAP_      |                 SWAP gate                        | `builder.SWAP(1, 2)`                                                    |
| CNOT       |    _CNOT_      |              Controlled-NOT gate                 | `builder.CNOT(1, 2)`                                                    |

### Non-Unitary Instructions

| Name       | Operator       | Description                                      | Example                                                                 |
|------------|----------------|--------------------------------------------------|-------------------------------------------------------------------------|
| [Init](https://qutech-delft.github.io/cQASM-spec/latest/language_specification/statements/instructions/non_unitary_instructions/init_instruction.html)          |     _init_        |               Initialize certain qubits in $\|0>$                      | `builder.init(0)`                                                         |
| [Measure](https://qutech-delft.github.io/cQASM-spec/latest/language_specification/statements/instructions/non_unitary_instructions/measure_instruction.html)          |     _measure_        |               Measure qubit argument                      | `builder.measure(0)`                                                   |
| [Reset](https://qutech-delft.github.io/cQASM-spec/latest/language_specification/statements/instructions/non_unitary_instructions/reset_instruction.html)          |     _reset_        |                  Reset a qubit's state to $\|0>$                         | `builder.reset(0)`                                                  |

### Control Instructions

| Name       | Operator       | Description                                      | Example                                                                 |
|------------|----------------|--------------------------------------------------|-------------------------------------------------------------------------|
| [Barrier](https://qutech-delft.github.io/cQASM-spec/latest/language_specification/statements/instructions/control_instructions/barrier_instruction.html)    |    _barrier_  |               Barrier gate                        | `builder.barrier(0)`                                                    |
| [Wait](https://qutech-delft.github.io/cQASM-spec/latest/language_specification/statements/instructions/control_instructions/wait_instruction.html)       |    _wait_     |               Wait gate                           | `builder.wait(0)`                                                       |