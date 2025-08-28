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

OpenSquirrel is a quantum compiler that chooses a _modular_, over a _configurable_,
approach to prepare and optimize quantum circuits for heterogeneous target architectures.

It has a user-friendly interface and is straightforwardly extensible with custom-made readers,
compiler passes, and exporters.
As a quantum circuit compiler,
it is fully aware of the semantics of each gate and arbitrary quantum gates can be constructed manually.
It supports the [cQASM](https://qutech-delft.github.io/cQASM-spec/latest/) quantum programming language,
using [libQASM](https://github.com/QuTech-Delft/libqasm) as language parser.
It is developed in modern Python and follows best practices.

## Installation

OpenSquirrel can be easily installed from PyPI.
We recommend using a virtual environment (_e.g._, venv).

```shell
$ pip install opensquirrel
```

To install the dependencies to run the examples on `jupyter`, install:

```shell
$ pip install opensquirrel[examples]
```

## Getting started

Once installed, the `opensquirrel` module can be imported accordingly:

```python
import opensquirrel
```

Essentially, compiling a quantum circuit in OpenSquirrel can be seen as a 3-stage process:
1. Defining and building the quantum circuit using either the `CircuitBuilder` or from a cQASM string.
2. Executing (multiple) compilation passes on the circuit,
each traversing and modifying it (_e.g._, decomposition of the gates).
3. Writing the circuit to cQASM or exporting it to a specific quantum circuit format.

Here is an example of building a circuit using the `CircuitBuilder`:

```python
from math import pi
from opensquirrel.circuit_builder import CircuitBuilder

# Initialize the builder and build your circuit
builder = CircuitBuilder(qubit_register_size=1)
builder.H(0).Z(0).Y(0).Rx(0, pi / 3)

# Get the circuit from the circuit builder
circuit = builder.to_circuit()
```

Alternatively, one can define the same circuit as a cQASM string:

```python
cqasm_string = ("""
    version 3.0

    qubit q

    H q
    Z q
    Y q
    Rx(1.0471976) q
""")

from opensquirrel.circuit import Circuit
circuit = Circuit.from_string(cqasm_string)
```

The circuit can then be decomposed using a decomposition strategy.
The different decomposition strategies can be found in the
[examples](https://github.com/QuTech-Delft/OpenSquirrel/tree/develop/example/tutorials).
In the example below, the circuit is decomposed using the Z-Y-Z decomposer.

```python
from opensquirrel.passes.decomposer.aba_decomposer import ZYZDecomposer

circuit.decompose(decomposer=ZYZDecomposer())
```

Once the circuit is decomposed, it can be written back to cQASM.
This is done by invoking the `writer` class, as can be seen below.

```python
from opensquirrel.writer import writer

writer.circuit_to_string(circuit)
```

The output is then given by the following cQASM string:

    version 3.0

    qubit[1] q

    Rz(3.1415927) q[0]
    Ry(1.5707963) q[0]
    Rz(3.1415927) q[0]
    Ry(3.1415927) q[0]
    Rz(1.5707963) q[0]
    Ry(1.0471976) q[0]
    Rz(-1.5707963) q[0]

> __*Note*__: The cQASM writer is the standard writer of OpenSquirrel.
> This means that the string representation of the `Circuit` object is by default a cQASM string. Moreover, simply printing the `Circuit` object will result in its cQASM string representation.

## Documentation

The [OpenSquirrel documentation](https://QuTech-Delft.github.io/OpenSquirrel/) is hosted through GitHub Pages.


## Contributing

The contribution guidelines and set up can be found
[here](https://github.com/QuTech-Delft/OpenSquirrel/blob/develop/CONTRIBUTING.md).


## Licensing

OpenSquirrel is licensed under the Apache License, Version 2.0. See
[LICENSE](https://github.com/QuTech-Delft/OpenSquirrel/blob/master/LICENSE.md) for the full license text.


## Authors

Quantum Inspire: [support@quantum-inspire.com](mailto:"support@quantum-inspire.com")
