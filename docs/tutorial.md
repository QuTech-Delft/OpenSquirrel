# Tutorial

## Installation

OpenSquirrel is available through the Python Package Index ([PyPI](<https://pypi.org/project/opensquirrel/>)).

Accordingly, installation is as easy as ABC:
```shell
$ pip install opensquirrel
```

You can check if the package is installed by importing it:
```python
import opensquirrel
```

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

The issue is that the CNOT expects a qubit as second input argument where an integer has been provided.

## Modifying a circuit

### Merging single qubit gates

All single-qubit gates appearing in a circuit can be merged by applying `merge_single_qubit_gates()` to the circuit.
Note that multi-qubit gates remain untouched and single-qubit gates are not merged across any multi-qubit gates.
The gate that results from the merger of single-qubit gates will, in general,
comprise an arbitrary rotation and, therefore, not be a known gate.
In OpenSquirrel an unrecognized gate is deemed _anonymous_.
When a circuit contains anonymous gates and is written to a cQASM string,
the semantic representation of the anonymous gate is exported.

!!! warning

    The semantic representation of an anonymous gate is not compliant
    [cQASM](https://qutech-delft.github.io/cQASM-spec), meaning that
    a cQASM parser, _e.g._ [libQASM](https://qutech-delft.github.io/libqasm/),
    will not recognize it as a valid statement.

```python
from opensquirrel.circuit_builder import CircuitBuilder
from opensquirrel.ir import Float
import math

builder = CircuitBuilder(1)
for _ in range(4):
    builder.Rx(0, math.pi / 4)
qc = builder.to_circuit()

qc.merge_single_qubit_gates()

print(qc)
```
_Output_:

    version 3.0

    qubit[1] q

    Anonymous gate: BlochSphereRotation(Qubit[0], axis=[1. 0. 0.], angle=3.14159, phase=0.0)

In the above example, OpenSquirrel has merged all the Rx gates together.
Yet, for now, OpenSquirrel does not recognize that this results in a single Rx
over the cumulated angle of the individual rotations.
Moreover, it does not recognize that the result corresponds to the X gate (up to a global phase difference).
At a later stage, we may want OpenSquirrel to recognize the resultant gate
in the case it is part of the set of known gates.

The gate set is, however, not immutable.
In the following section, we demonstrate how new gates can be defined and added to the default gate set.

### Defining your own quantum gates

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
For instance, the CNOT gate is defined in the default gate set of OpenSquirrel as follows:

```python
from opensquirrel.ir import Gate, ControlledGate, QubitLike, named_gate
from opensquirrel.default_instructions import X

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

### Gate decomposition

OpenSquirrel can decompose the gates of a quantum circuit, given a specific decomposition.
OpenSquirrel offers several, so-called, decomposers out of the box,
but users can also make their own decomposer and apply them to the circuit.
Decompositions can be:
   1. predefined, or;
   2. inferred from the gate semantics.

#### 1. Predefined decomposition

The first kind of decomposition is when you want to replace a particular gate in the circuit,
like the CNOT gate, with a fixed list of gates.
It is commonly known that CNOT can be decomposed as H-CZ-H.
This decomposition is demonstrated below using a Python _lambda function_,
which requires the same parameters as the gate that is decomposed:

```python
from opensquirrel.circuit import Circuit
from opensquirrel.default_instructions import CNOT, H, CZ

qc = Circuit.from_string(
    """
    version 3.0
    qubit[3] q

    X q[0:2]  // Note that this notation is expanded in OpenSquirrel.
    CNOT q[0], q[1]
    Ry q[2], 6.78
    """
)
qc.replace(
    CNOT,
    lambda control, target:
    [
        H(target),
        CZ(control, target),
        H(target),
    ]
)

print(qc)
```
_Output_:

    version 3.0

    qubit[3] q

    X q[0]
    X q[1]
    X q[2]
    H q[1]
    CZ q[0], q[1]
    H q[1]
    Ry(6.78) q[2]

OpenSquirrel will check whether the provided decomposition is correct.
For instance, an exception is thrown if we forget the final Hadamard,
or H gate, in our custom-made decomposition:

```python
from opensquirrel.circuit import Circuit
from opensquirrel.default_instructions import CNOT, CZ, H

qc = Circuit.from_string(
    """
    version 3.0
    qubit[3] q

    X q[0:2]
    CNOT q[0], q[1]
    Ry q[2], 6.78
    """
)
try:
    qc.replace(
        CNOT,
        lambda control, target:
        [
            H(target),
            CZ(control, target),
        ]
    )
except Exception as e:
  print(e)
```
_Output_:

    replacement for gate CNOT does not preserve the quantum state

#### 2. Inferred decomposition

OpenSquirrel has a variety inferred decomposition strategies.
More in depth tutorials can be found in the [decomposition example Jupyter notebook](https://github.com/QuTech-Delft/OpenSquirrel/blob/develop/example/decompositions.ipynb).

One of the most common single qubit decomposition techniques is the Z-Y-Z decomposition.
This technique decomposes a quantum gate into an `Rz`, `Ry` and `Rz` gate in that order.
The decompositions are found in `opensquirrel.passes.decomposer`,
an example can be seen below where a Hadamard, Z, Y and Rx gate are all decomposed on a single qubit circuit.

```python
from opensquirrel.circuit_builder import CircuitBuilder
from opensquirrel.passes.decomposer import ZYZDecomposer
from opensquirrel.ir import Float
import math

builder = CircuitBuilder(qubit_register_size=1)
builder.H(0).Z(0).Y(0).Rx(0, math.pi / 3)
qc = builder.to_circuit()

qc.decompose(decomposer=ZYZDecomposer())

print(qc)
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
from opensquirrel.default_instructions import H

print(ZYZDecomposer().decompose(H(0)))
```
_Output_:

    [BlochSphereRotation(Qubit[0], axis=Axis[0. 0. 1.], angle=1.5707963267948966, phase=0.0),
     BlochSphereRotation(Qubit[0], axis=Axis[0. 1. 0.], angle=1.5707963267948966, phase=0.0),
     BlochSphereRotation(Qubit[0], axis=Axis[0. 0. 1.], angle=1.5707963267948966, phase=0.0)]


## Exporting a circuit

As you have seen in the examples above, you can turn a circuit into a
[cQASM](https://qutech-delft.github.io/cQASM-spec) string
by simply using the `str` or `__repr__` methods.
We are aiming to support the possibility to export to other languages as well,
_e.g._, a OpenQASM 3.0 string, and frameworks, _e.g._, a Qiskit quantum circuit.
