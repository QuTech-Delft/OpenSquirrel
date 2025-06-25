Once we have [created a circuit](creating-a-circuit.md), we can now perform actions on it by applying various
compilation passes.
The actions that were listed in the general [tutorial](index.md) correspond to the following types of compilation
(in alphabetic order):

- [Decomposition](../compilation-passes/types-of-passes/decomposition/index.md)
- [Exporting](../compilation-passes/types-of-passes/exporting/index.md)
- [Mapping](../compilation-passes/types-of-passes/mapping/index.md)
- [Merging](../compilation-passes/types-of-passes/merging/index.md)
- [Routing](../compilation-passes/types-of-passes/routing/index.md)
- [Validation](../compilation-passes/types-of-passes/validation/index.md)

All available compilation passes, organized by type, can be found [here](../compilation-passes/index.md).

### Input program

In this section, we will go through a few compilation passes by applying them to an input program and evaluating the
result after each pass.
We will use the following example program, from which we can create the `circuit` object as described in
[Creating a circuit](creating-a-circuit.md):

!!! example "Example input program"

    Program as a cQASM string:

    ```linenums="1"
    version 3.0

    qubit[3] q
    bit[2] b

    init q

    Ry(pi/2) q[0]
    X q[0]
    CNOT q[0], q[2]

    barrier q
    b[0, 1] = measure q[0, 2]

    ```

    Program as described by the `circuit` object in OpenSquirrel:

    `print(circuit)`

    ```
    version 3.0

    qubit[3] q
    bit[2] b

    init q[0]
    init q[1]
    init q[2]
    Ry(1.5707963) q[0]
    X q[0]
    CNOT q[0], q[2]
    barrier q[0]
    barrier q[1]
    barrier q[2]
    b[0] = measure q[0]
    b[1] = measure q[2]
    ```

### Target QPU specifications

connectivity

```python
connectivity= {
    "0": [1],
    "1": [0, 2],
    "2": [1]
}
```

primitive gate set, labeled as the `pgs`:

```python
pgs = ["I", "X90", "Rx", "Rz", "CZ"]
```

## Routing

We start the compilation process with an initial routing pass to ensure that the interactions in the circuit occur
between neighbouring qubits.
The example circuit contains a two-qubit gate, _i.e._ the CNOT gate, between qubits at indices `0` and `2`,
respectively.
Given the connectivity of the QPU as stated above, we see that these qubits are not connected and therefore cannot
interact.
By introducing SWAPs in the circuit, the routing pass will ensure that all interactions in the circuit occur
between neighbouring qubits.

Here we use the [`ShortestPathRouter`](../compilation-passes/types-of-passes/routing/shortest-path-router.md) to route
the circuit.

```python
from opensquirrel.passes.router import ShortestPathRouter

circuit.route(router=ShortestPathRouter(connectivity=connectivity))
```

??? example "`print(circuit)  # Circuit after routing`"

    ```
    version 3.0

    qubit[3] q
    bit[2] b

    init q[0]
    init q[1]
    init q[2]
    Ry(1.5707963) q[0]
    X q[0]
    SWAP q[1], q[2]
    CNOT q[0], q[1]
    barrier q[0]
    barrier q[2]
    barrier q[1]
    b[0] = measure q[0]
    b[1] = measure q[1]
    ```

Note that, in general, a routing pass will require the connectivity of the QPU as input.

!!! warning ""

    Since a routing pass will introduce SWAPs to the circuit,
    this pass needs to be done before any decomposition passes,
    as SWAPs are generally not supported by the QPU, _i.e._ they are not in the primitive gate set.

## Decomposition - predefined

```python
from opensquirrel.passes.decomposer import SWAP2CZDecomposer

circuit.decompose(decomposer=SWAP2CZDecomposer())
```

??? example "`print(circuit)  # Circuit after SWAP to CZ decomposition`"

    ```
    version 3.0

    qubit[3] q
    bit[2] b

    init q[0]
    init q[1]
    init q[2]
    Ry(1.5707963) q[0]
    X q[0]
    Ry(-1.5707963) q[2]
    CZ q[1], q[2]
    Ry(1.5707963) q[2]
    Ry(-1.5707963) q[1]
    CZ q[2], q[1]
    Ry(1.5707963) q[1]
    Ry(-1.5707963) q[2]
    CZ q[1], q[2]
    Ry(1.5707963) q[2]
    CNOT q[0], q[1]
    barrier q[0]
    barrier q[2]
    barrier q[1]
    b[0] = measure q[0]
    b[1] = measure q[1]
    ```

```python
from opensquirrel.passes.decomposer import CNOT2CZDecomposer

circuit.decompose(decomposer=CNOT2CZDecomposer())
```

??? example "`print(circuit)  # Circuit after CNOT to CZ decomposition`"

    ```
    version 3.0

    qubit[3] q
    bit[2] b

    init q[0]
    init q[1]
    init q[2]
    Ry(1.5707963) q[0]
    X q[0]
    Ry(-1.5707963) q[2]
    CZ q[1], q[2]
    Ry(1.5707963) q[2]
    Ry(-1.5707963) q[1]
    CZ q[2], q[1]
    Ry(1.5707963) q[1]
    Ry(-1.5707963) q[2]
    CZ q[1], q[2]
    Ry(1.5707963) q[2]
    Ry(-1.5707963) q[1]
    CZ q[0], q[1]
    Ry(1.5707963) q[1]
    barrier q[0]
    barrier q[2]
    barrier q[1]
    b[0] = measure q[0]
    b[1] = measure q[1]
    ```

## Merging

Merging single qubit gates

```python
from opensquirrel.passes.merger import SingleQubitGatesMerger

circuit.merge(merger=SingleQubitGatesMerger())
```

??? example "`print(circuit)  # Circuit after merging single-qubit gates`"

    ```
    version 3.0

    qubit[3] q
    bit[2] b

    init q[0]
    init q[1]
    init q[2]
    Rn(0.0, -1.0, 0.0, 1.5707963, 0.0) q[2]
    CZ q[1], q[2]
    Ry(1.5707963) q[2]
    Rn(0.0, -1.0, 0.0, 1.5707963, 0.0) q[1]
    CZ q[2], q[1]
    Ry(1.5707963) q[1]
    Rn(0.0, -1.0, 0.0, 1.5707963, 0.0) q[2]
    CZ q[1], q[2]
    H q[0]
    Rn(0.0, -1.0, 0.0, 1.5707963, 0.0) q[1]
    CZ q[0], q[1]
    Ry(1.5707963) q[1]
    Ry(1.5707963) q[2]
    barrier q[0]
    barrier q[2]
    barrier q[1]
    b[0] = measure q[0]
    b[1] = measure q[1]
    ```

## Decomposition - inferred

```python
from opensquirrel.passes.decomposer import McKayDecomposer

circuit.decompose(decomposer=McKayDecomposer())
```

??? example "`print(circuit)  # Circuit after McKay decomposition`"

    ```
    version 3.0

    qubit[3] q
    bit[2] b

    init q[0]
    init q[1]
    init q[2]
    Rz(1.5707963) q[2]
    X90 q[2]
    Rz(-1.5707963) q[2]
    CZ q[1], q[2]
    Rz(-1.5707963) q[2]
    X90 q[2]
    Rz(1.5707963) q[2]
    Rz(1.5707963) q[1]
    X90 q[1]
    Rz(-1.5707963) q[1]
    CZ q[2], q[1]
    Rz(-1.5707963) q[1]
    X90 q[1]
    Rz(1.5707963) q[1]
    Rz(1.5707963) q[2]
    X90 q[2]
    Rz(-1.5707963) q[2]
    CZ q[1], q[2]
    Rz(1.5707963) q[0]
    X90 q[0]
    Rz(1.5707963) q[0]
    Rz(1.5707963) q[1]
    X90 q[1]
    Rz(-1.5707963) q[1]
    CZ q[0], q[1]
    Rz(-1.5707963) q[1]
    X90 q[1]
    Rz(1.5707963) q[1]
    Rz(-1.5707963) q[2]
    X90 q[2]
    Rz(1.5707963) q[2]
    barrier q[0]
    barrier q[2]
    barrier q[1]
    b[0] = measure q[0]
    b[1] = measure q[1]
    ```

More in depth tutorials can be found in the [decomposition example Jupyter notebook](https://github.com/QuTech-Delft/OpenSquirrel/blob/develop/example/decompositions.ipynb).

## Validation

Interaction

```python
from opensquirrel.passes.validator import RoutingValidator

circuit.validate(RoutingValidator(connectivity=connectivity))
```

For instance, the `RoutingValidator` checks whether a circuit is directly executable given some hardware's coupling map.

Primitive gate set

```python
from opensquirrel.passes.validator import PrimitiveGateValidator

circuit.validate(PrimitiveGateValidator(pgs=pgs))
```

## Exporting

Exporter (or Write it out)
