# OpenSquirrel: a flexible quantum program compiler.

![CI](https://github.com/QuTech-Delft/OpenSquirrel/actions/workflows/tests.yaml/badge.svg)
[![pypi](https://img.shields.io/pypi/v/opensquirrel.svg)](https://pypi.org/project/opensquirrel/)
[![image](https://img.shields.io/pypi/pyversions/opensquirrel.svg)](https://pypi.python.org/pypi/opensquirrel)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![pytest](https://img.shields.io/badge/py-test-blue?logo=pytest)](https://github.com/pytest-dev/pytest)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

```
 ,;;:;,
   ;;;;;
  ,:;;:;    ,'=.
  ;:;:;' .=" ,'_\
  ':;:;,/  ,__:=@
   ';;:;  =./)_
 jgs `"=\_  )_"`
          ``'"`
```

OpenSquirrel is a quantum compiler that chooses a _modular_, over a _configurable_, approach to prepare and optimize quantum circuits for heterogeneous target architectures.

It has a user-friendly interface and is straightforwardly extensible with custom-made readers, compiler passes, and exporters.
As a quantum circuit compiler, it is fully aware of the semantics of each gate and arbitrary quantum gates can be constructed manually.
It understands the quantum programming language cQASM 3 and will support additional quantum programming languages in the future.
It is developed in modern Python and follows best practices.

## Installation

We encourage installing OpenSquirrel via `pip`:

```shell
$ pip install opensquirrel
```

To install the dependencies to run the examples on `jupyter`, install:

```shell
$ pip install opensquirrel[examples]
```

The tutorials can be found [here](https://github.com/QuTech-Delft/OpenSquirrel/tree/develop/example).

## Getting started

Essentially, compiling a circuit in OpenSquirrel can be seen as a 3-stage process:
1. Defining and building the quantum circuit using either the `CircuitBuilder` or from a `cQASM` string.
2. Executing multiple passes on the circuit, each traversing and modifying it (e.g., a decomposition).
3. Exporting the circuit (to `cQASM` again, or to a _lowered_ language like QuantifyScheduler). 

Here is an example of building a circuit using the `CircuitBuilder`:

```python
import math
from opensquirrel.circuit_builder import CircuitBuilder
from opensquirrel.ir import Qubit, Float

# Tell the circuit builder how you want your circuit
builder = CircuitBuilder(qubit_register_size=1)
builder.H(Qubit(0))
builder.Z(Qubit(0))
builder.Y(Qubit(0))
builder.Rx(Qubit(0), Float(math.pi / 3))

# Get the circuit from the circuit builder
circuit = builder.to_circuit()

cqasm_string = (
"""
version 3.0

qubit[1] q

H q[0]
Z q[0]
Y q[0]
Rx(1.0471976) q[0]
""")

qc = Circuit.from_string(cqasm_string)
```

The circuit can then be decomposed using a decomposition strategy. The different decomposition strategies can be found in the [tutorials](https://github.com/QuTech-Delft/OpenSquirrel/tree/develop/example/tutorials).
In the example below, the circuit is decomposed using `ZYZDecomposer`.

```python
from opensquirrel.decomposer.aba_decomposer import ZYZDecomposer

circuit.decompose(decomposer=ZYZDecomposer())
```

Once the circuit is decomposed, the circuit is written to low level assembly language, namely `cQASM3`. This is done by
invoking the `writer` class, as can be seen below.

```python
from opensquirrel.writer import writer

writer.circuit_to_string(circuit)
The output is then the following `cQASM3` string.
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

## Documentation

OpenSquirrel documentation is hosted through GitHub Pages [here](https://QuTech-Delft.github.io/OpenSquirrel/).
The [example](https://github.com/QuTech-Delft/OpenSquirrel/tree/develop/example) folder contains `Jupyter` notebooks with
example tutorials.

## Contributing

The contribution guidelines and set up can be found
[here](https://github.com/QuTech-Delft/OpenSquirrel/blob/develop/CONTRIBUTING.md).

## Authors

Quantum Inspire: [support@quantum-inspire.com](mailto:"support@quantum-inspire.com")
