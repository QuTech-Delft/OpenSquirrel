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
The tutorials can be found in [here](https://github.com/QuTech-Delft/OpenSquirrel/tree/develop/example).

## Getting started
Essentially, compiling a circuit in OpenSquirrel requires,
1. Defining and building a quantum circuit
2. Decomposing a circuit
3. Writing the circuit to assembly

The circuit can be built with the `CircuitBuilder` class. Here is an example of building a single qubit circuit that
includes a Hadamard gate, a Z gate, a Y gate, and a rotation X gate.
```python
import math
from opensquirrel.circuit_builder import CircuitBuilder
from opensquirrel.ir import Qubit, Float

# Build the circuit structure using the CircuitBuilder
builder = CircuitBuilder(qubit_register_size=1)
builder.H(Qubit(0))
builder.Z(Qubit(0))
builder.Y(Qubit(0))
builder.Rx(Qubit(0), Float(math.pi / 3))

# Create a new circuit from the constructed structure
circuit = builder.to_circuit()
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
```
The output is then the following `cQASM3` string.
```
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


## Authors

Quantum Inspire: [support@quantum-inspire.com](mailto:"support@quantum-inspire.com")
