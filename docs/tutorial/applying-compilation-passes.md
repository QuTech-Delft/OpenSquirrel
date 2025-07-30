Once we have [created a circuit](creating-a-circuit.md), we can now perform actions on it by applying various
compilation passes.
The actions that were listed in the general [tutorial](index.md) correspond to the following types of compilation
(in alphabetic order):

- [Decomposition](../compilation-passes/decomposition/index.md)
- [Exporting](../compilation-passes/exporting/index.md)
- [Mapping](../compilation-passes/mapping/index.md)
- [Merging](../compilation-passes/merging/index.md)
- [Routing](../compilation-passes/routing/index.md)
- [Validation](../compilation-passes/validation/index.md)

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

    ```linenums="1"
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

The purpose of compilation is to be able to execute the user-described program on a particular target quantum processing
unit (QPU), also refer to as the target backend.
A target backend will have some specific properties that are required by certain compilation passes as input parameters.

Here we define an example connectivity and primitive gate set, that will be needed for some of the following passes.

#### Connectivity

The connectivity of a QPU describes which qubits are connected and can, therefore, interact with each other.
This is essential information for two-qubit gates, as they can only occur between qubits that share a connection.

The connectivity is given by a dictionary, where the keys are the qubit indices and the values are a list of qubit
indices that the qubit has a (uni-directional) connection with.

```python
connectivity= {
    "0": [1],
    "1": [0, 2],
    "2": [1]
}
```

!!! note "Bi-directional connections"

    Connections are bi-directional, only if defined explicitly so,
    _i.e._, the connection between qubits `i` and `j` is bi-directional if qubit `i` is connected to qubit `j` and qubit
    `j` is connected to qubit `i`.

We will use the connectivity when routing the circuit and perform a final validation to check that the interactions
occur between connected qubits.

#### Primitive gate set

The primitive gate set describes the set of gates that are supported by the (lower-level software of the) target
backend.
The primitive gates are not to be confused with the native gates.
The latter are the gates that can directly be performed on the QPU, _i.e._, they are _native_ to the QPU.
In general, a translation step will still occur from the primitive gates to the native gates, _on the side_ of the
target backend.

The primitive gate set, labeled as the `pgs`, is given by a list of gate names
(as they are defined in the
[cQASM standard gate library](https://qutech-delft.github.io/cQASM-spec/latest/standard_gate_set/index.html)):

```python
pgs = ["I", "X90", "Rx", "Rz", "CZ", "init", "barrier", "measure"]
```

A target backend expects that the circuit of the compiled program consists solely of gates that appear in the primitive
gate set.
Accordingly, we will use `pgs` as an input argument to validate that the fully decomposed circuit is in terms of gates
that are in the primitive gate set.

## Routing

We start the compilation process with an initial routing pass to ensure that the interactions in the circuit occur
between neighbouring qubits.
The example circuit contains a two-qubit gate, _i.e._ the CNOT gate, between qubits at indices `0` and `2`,
respectively.
Given the _connectivity_ of the QPU as stated above, we see that these qubits are not connected and therefore cannot
interact.
By introducing SWAPs in the circuit, the routing pass will ensure that all interactions in the circuit occur
between neighbouring qubits.

Here we use the `route` method with the
[shortest path router](../compilation-passes/routing/shortest-path-router.md) `ShortestPathRouter`
to route the circuit.

```python
from opensquirrel.passes.router import ShortestPathRouter

circuit.route(router=ShortestPathRouter(connectivity=connectivity))
```

??? example "`print(circuit)  # Circuit after routing`"

    ```linenums="1"
    version 3.0

    qubit[3] q
    bit[2] b

    init q[0]
    init q[1]
    init q[2]
    Ry(1.5707963) q[0]
    X q[0]
    SWAP q[0], q[1]
    CNOT q[1], q[2]
    barrier q[1]
    barrier q[0]
    barrier q[2]
    b[0] = measure q[1]
    b[1] = measure q[2]
    ```

Note that, in general, a routing pass will require the _connectivity_ of the QPU as input.

!!! warning ""

    Since a routing pass will introduce SWAPs to the circuit,
    it will need to be applied before any decomposition passes,
    as SWAPs are generally not supported by the QPU.

## Decomposition - predefined

We will continue with some _predefined_ decompositions. They are _predefined_ in the sense that the decomposition is
defined for a particular gate, _e.g._ the SWAP gate, and the resultant decomposition is hard-coded.

SWAP gates are generally not supported by the target backend (consider the `pgs`) and need to be decomposed into,
_e.g._, a series of CZ gates and single-qubit gates.

!!! note

    Currently, OpenSquirrel only has general decomposers for arbitrary two-qubit controlled-gates, _i.e_, the

    - the [CNOT decomposer](../compilation-passes/decomposition/cnot-decomposer.md) (`CNOTDecomposer`),
    and
    - the [CZ decomposer](../compilation-passes/decomposition/cz-decomposer.md) (`CZDecomposer`).

    Since the SWAP gate is not a controlled-gate, the predefined
    [SWAP-to-CNOT or SWAP-to-CZ decomposers](../compilation-passes/decomposition/predefined-decomposers.md)
    are to be used to decompose a SWAP gate to a series of single-qubit gates and, either,
    CZs or CNOTs for two-qubit interactions.

Since the CZ gate _is_ supported by the target backend, we use the `decompose` method with the
[SWAP-to-CZ decomposer](../compilation-passes/decomposition/predefined-decomposers.md)
(`SWAP2CZDecomposer`) to decompose the SWAP gate.

```python
from opensquirrel.passes.decomposer import SWAP2CZDecomposer

circuit.decompose(decomposer=SWAP2CZDecomposer())
```

??? example "`print(circuit)  # Circuit after SWAP-to-CZ decomposition`"

    ```linenums="1"
    version 3.0

    qubit[3] q
    bit[2] b

    init q[0]
    init q[1]
    init q[2]
    Ry(1.5707963) q[0]
    X q[0]
    Ry(-1.5707963) q[1]
    CZ q[0], q[1]
    Ry(1.5707963) q[1]
    Ry(-1.5707963) q[0]
    CZ q[1], q[0]
    Ry(1.5707963) q[0]
    Ry(-1.5707963) q[1]
    CZ q[0], q[1]
    Ry(1.5707963) q[1]
    CNOT q[1], q[2]
    barrier q[1]
    barrier q[0]
    barrier q[2]
    b[0] = measure q[1]
    b[1] = measure q[2]
    ```

Our example circuit also contains a CNOT gate.
Since it is not supported by the target backend, we use the `decompose` method with the
[CNOT-to-CZ](../compilation-passes/decomposition/predefined-decomposers.md) predefined decomposer
(`CNOT2CZDecomposer`) to decompose the CNOT into a series of single-qubit gates and a CZ gate.

```python
from opensquirrel.passes.decomposer import CNOT2CZDecomposer

circuit.decompose(decomposer=CNOT2CZDecomposer())
```

??? example "`print(circuit)  # Circuit after CNOT-to-CZ decomposition`"

    ```linenums="1"
    version 3.0

    qubit[3] q
    bit[2] b

    init q[0]
    init q[1]
    init q[2]
    Ry(1.5707963) q[0]
    X q[0]
    Ry(-1.5707963) q[1]
    CZ q[0], q[1]
    Ry(1.5707963) q[1]
    Ry(-1.5707963) q[0]
    CZ q[1], q[0]
    Ry(1.5707963) q[0]
    Ry(-1.5707963) q[1]
    CZ q[0], q[1]
    Ry(1.5707963) q[1]
    Ry(-1.5707963) q[2]
    CZ q[1], q[2]
    Ry(1.5707963) q[2]
    barrier q[1]
    barrier q[0]
    barrier q[2]
    b[0] = measure q[1]
    b[1] = measure q[2]
    ```

Since the CNOT is a controlled-gate, we could also have used the
[CZ decomposer](../compilation-passes/decomposition/cz-decomposer.md) to achieve the same result.
Nevertheless, if available, a predefined decomposer will generally be more efficient as no inference is required.

## Merging

To reduce the amount of single-qubit gates in the circuit,
we can merge consecutive single-qubit gates on the same qubit into one.
To do so, we use the `merge` method with the
[single-qubit gates merger](../compilation-passes/merging/single-qubit-gates-merger.md) pass
(`SingleQubitGatesMerger`).

!!! note

    The single-qubit gate that results from merging multiple single-qubit gates, is generally not supported by the
    target backend; a single-qubit gate decomposition pass will need to be applied after merging.
    OpenSquirrel will check if the resultant gate is equal (up to a global phase) to the gates that it replaces.

```python
from opensquirrel.passes.merger import SingleQubitGatesMerger

circuit.merge(merger=SingleQubitGatesMerger())
```

??? example "`print(circuit)  # Circuit after merging single-qubit gates`"

    ```linenums="1"
    version 3.0

    qubit[3] q
    bit[2] b

    init q[0]
    init q[1]
    init q[2]
    H q[0]
    Rn(0.0, -1.0, 0.0, 1.5707963, 0.0) q[1]
    CZ q[0], q[1]
    Ry(1.5707963) q[1]
    Rn(0.0, -1.0, 0.0, 1.5707963, 0.0) q[0]
    CZ q[1], q[0]
    Ry(1.5707963) q[0]
    Rn(0.0, -1.0, 0.0, 1.5707963, 0.0) q[1]
    CZ q[0], q[1]
    Ry(1.5707963) q[1]
    Rn(0.0, -1.0, 0.0, 1.5707963, 0.0) q[2]
    CZ q[1], q[2]
    Ry(1.5707963) q[2]
    barrier q[1]
    barrier q[0]
    barrier q[2]
    b[0] = measure q[1]
    b[1] = measure q[2]
    ```

## Decomposition - inferred

To ensure that the single-qubit gates in the circuit can be executed on the target backend,
we need to decompose them according to available gates in the primitive gate set, _i.e._, the `pgs`.
We can see from `pgs` that our target backend accepts all kinds of rotations about the _x_- and _z_- axis.

The McKay decomposer decomposes arbitrary single-qubit gates into _at most_ 5 gates:
$R_z(\gamma)\cdot X^{1/2}\cdot R_z(\beta)\cdot X^{1/2}\cdot R_z(\alpha)$,
where $\alpha$, $\beta$, and $\gamma$, represent different rotation angles.
The rotation angles need to be _inferred_ from the semantic of the single-qubit gate that is to be decomposed, _i.e._,
they are not defined in advance.

We invoke the McKay decomposition on the circuit by applying the `decompose` method with the
[McKay decomposer](../compilation-passes/decomposition/mckay-decomposer.md) pass (`McKayDecomposer`).

```python
from opensquirrel.passes.decomposer import McKayDecomposer

circuit.decompose(decomposer=McKayDecomposer())
```

??? example "`print(circuit)  # Circuit after McKay decomposition`"

    ```linenums="1"
    version 3.0

    qubit[3] q
    bit[2] b

    init q[0]
    init q[1]
    init q[2]
    Rz(1.5707963) q[0]
    X90 q[0]
    Rz(1.5707963) q[0]
    Rz(1.5707963) q[1]
    X90 q[1]
    Rz(-1.5707963) q[1]
    CZ q[0], q[1]
    Rz(1.5707963) q[0]
    Rz(-1.5707963) q[1]
    X90 q[1]
    Rz(1.5707963) q[1]
    Rz(1.5707963) q[0]
    X90 q[0]
    Rz(-1.5707963) q[0]
    CZ q[1], q[0]
    Rz(-1.5707963) q[1]
    Rz(-1.5707963) q[0]
    X90 q[0]
    Rz(1.5707963) q[0]
    Rz(1.5707963) q[1]
    X90 q[1]
    Rz(-1.5707963) q[1]
    CZ q[0], q[1]
    Rz(1.5707963) q[0]
    Rz(-1.5707963) q[1]
    X90 q[1]
    Rz(1.5707963) q[1]
    Rz(1.5707963) q[2]
    X90 q[2]
    Rz(-1.5707963) q[2]
    CZ q[1], q[2]
    Rz(-2.3561945) q[1]
    Rz(-1.5707963) q[2]
    X90 q[2]
    Rz(1.5707963) q[2]
    barrier q[1]
    barrier q[0]
    barrier q[2]
    b[0] = measure q[1]
    b[1] = measure q[2]
    ```

## Validation

It is good practice to validate certain properties of the program before exporting it.
Here we check whether the interactions in the final circuit are valid given the _connectivity_ and
whether all gates appear in the _primitive gate set_.

Even though, [validation](../compilation-passes/validation/index.md) is not a compilation pass _per se_,
it is called in the same way on the circuit.
Accordingly, we treat it as a pass that is part of the compilation pass library.

### Routing validation

To check the validity of the interactions in the circuit, we use the `validate` method with the
[interactions validator](../compilation-passes/validation/interaction-validator.md) pass
(`InteractionValidator`) and the _connectivity_ as an input argument for the validator.

```python
from opensquirrel.passes.validator import InteractionValidator

circuit.validate(validator=InteractionValidator(connectivity=connectivity))
```

An exception will be thrown if any interaction in the circuit is invalid.

### Primitive gate set validation

To check if all gates in the circuit are part of the primitive gate set, we use the `validate` method with the
[primitive gate validator](../compilation-passes/validation/primitive-gate-validator.md) pass
(`PrimitiveGateValidator`) and the `pgs`, _i.e. primitive gate set_, as an input argument for the validator.

```python
from opensquirrel.passes.validator import PrimitiveGateValidator

circuit.validate(validator=PrimitiveGateValidator(primitive_gate_set=pgs))
```

An exception will be thrown if any gate is not part of the _primitive gate set_.

## Exporting

Now that we have the performed the desired compilation passes and validated certain aspects of the circuit,
we can either choose to write it out to cQASM or export it to a different format.

Proceed to [Writing out and exporting](writing-out-and-exporting.md) to learn how.


## _Full example compilation_

Find below the full example compilation procedure in a single Python script (including reading and writing out of the
program).

??? example "Full example compilation"

    The Python script, taking as input the example program:

    ```python

    from opensquirrel import Circuit
    from opensquirrel.passes.router import ShortestPathRouter
    from opensquirrel.passes.decomposer import SWAP2CZDecomposer, CNOT2CZDecomposer, McKayDecomposer
    from opensquirrel.passes.merger import SingleQubitGatesMerger
    from opensquirrel.passes.validator import RoutingValidator, PrimitiveGateValidator

    # Target QPU specifications
    connectivity= {
        "0": [1],
        "1": [0, 2],
        "2": [1]
    }
    pgs = ["I", "X", "Z", "X90", "mX90", "S", "Sdag", "T", "Tdag", "Rx", "Rz", "CZ"]

    # Reading the example program
    circuit = Circuit.from_string(
        """
        version 3.0

        qubit[3] q
        bit[2] b

        init q

        Ry(pi/2) q[0]
        X q[0]
        CNOT q[0], q[2]

        barrier q
        b[0, 1] = measure q[0, 2]
        """
    )

    # Applying compilation passes (to the circuit)
    circuit.route(router=ShortestPathRouter(connectivity=connectivity))
    circuit.decompose(decomposer=SWAP2CZDecomposer())
    circuit.decompose(decomposer=CNOT2CZDecomposer())
    circuit.merge(merger=SingleQubitGatesMerger())
    circuit.decompose(decomposer=McKayDecomposer())

    # Validating circuit aspects
    circuit.validate(validator=RoutingValidator(connectivity=connectivity))
    circuit.validate(validator=PrimitiveGateValidator(pgs=pgs))

    # Writing out the compiled program to cQASM (one can also use the 'str()' method)
    print(circuit)

    ```

    The compiled program (in cQASM):

    ```linenums="1"
    version 3.0

    qubit[3] q
    bit[2] b

    init q[0]
    init q[1]
    init q[2]
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
    Rz(1.5707963) q[0]
    X90 q[0]
    Rz(-1.5707963) q[0]
    CZ q[1], q[0]
    Rz(-1.5707963) q[0]
    X90 q[0]
    Rz(1.5707963) q[0]
    Rz(1.5707963) q[1]
    X90 q[1]
    Rz(-1.5707963) q[1]
    CZ q[0], q[1]
    Rz(-1.5707963) q[1]
    X90 q[1]
    Rz(1.5707963) q[1]
    Rz(1.5707963) q[2]
    X90 q[2]
    Rz(-1.5707963) q[2]
    CZ q[1], q[2]
    Rz(-1.5707963) q[2]
    X90 q[2]
    Rz(1.5707963) q[2]
    barrier q[1]
    barrier q[0]
    barrier q[2]
    b[0] = measure q[1]
    b[1] = measure q[2]
    ```
