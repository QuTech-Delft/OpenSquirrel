# Predefined Decomposition

The first kind of decomposition is when you want to replace a particular gate in the circuit,
like the `CNOT` gate, with a fixed list of gates.
It is commonly known that `CNOT` can be decomposed as `H`-`CZ`-`H`.
This decomposition is demonstrated below using a Python _lambda function_,
which requires the same parameters as the gate that is decomposed:

```python
from opensquirrel.circuit import Circuit
from opensquirrel import CNOT, H, CZ

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
from opensquirrel import CNOT, CZ, H

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

## _`CNOT` to `CZ` decomposer_

The decomposition of the `CNOT` gate into a `CZ` gate (with additional single-qubit gates) is used frequently.
To this end a `CNOT2CZDecomposer` has been implemented that decomposes any `CNOT`s in a circuit to a
`Ry(-π/2)`-`CZ`-`Ry(π/2)`. The decomposition is illustrated in the image below.

<p align="center"> <img width="600" src="decomposition/_static/cnot2cz.png"> </p>

`Ry` gates are used instead of, _e.g._, `H` gates, as they are, generally,
more likely to be supported already by target backends.

## _`SWAP` to `CNOT` decomposer_

The `SWAP2CNOTDecomposer` implements the predefined decomposition of the `SWAP` gate into 3 `CNOT` gates.
The decomposition is illustrated in the image below.

<p align="center"> <img width="600" src="decomposition/_static/swap2cnot.png"> </p>

## _`SWAP` to `CZ` decomposer_

The `SWAP2CZDecomposer` implements the predefined decomposition of the `SWAP` gate into `Ry` rotations and 3 `CZ`
gates.
The decomposition is illustrated in the image below.

<p align="center"> <img width="600" src="decomposition/_static/swap2cz.png"> </p>
