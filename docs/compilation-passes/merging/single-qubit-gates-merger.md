All single-qubit gates appearing in a circuit can be merged by using the single-qubit gates merging pass
(`SingleQubitGatesMerger`).
Note that multi-qubit gates remain untouched and single-qubit gates are not merged across any multi-qubit gates.
Single-qubit gates are also not merged across _non-unitary_ instructions, _e.g._ `init`, `reset`, and `measure`,
and _control_ instructions, _e.g._, `wait`, and `barrier`.
Merging single-qubit gates may lead to a significant reduction in circuit depth, _i.e._,
the number of operations required to execute the circuit.

OpenSquirrel will try to recognize whether the resulting gate is a _known_ gate, _e.g._,
if two consecutive X90 gates are merged, OpenSquirrel will recognize it as a single X gate.
Nevertheless, the gate that results from the merger of multiple single-qubit gates will,
in general, be an arbitrary rotation.
Accordingly, to be able to run the circuit on a particular backend that supports a given primitive gate set,
it is often required to perform a [decomposition](../decomposition/index.md) pass after merging the single-qubit
gates.

!!! note

    Depending on the circuit and chosen decomposition, the circuit depth might actually increase,
    even though a merging pass has been applied.
    For instance, if the merging of two single-qubit gates leads to an arbitrary single-qubit rotation gate
    and the [`McKayDecomposer`](../decomposition/mckay-decomposer.md) is used, then the two initial gates may
    ultimately result in five single-qubit rotation gates.
    This is demonstrated in the final example below.

The example below shows how the single-qubit gates merging pass can be used to merge the single-qubit gates in the
circuit.
Note that the `SingleQubitGatesMerger` pass does not require any input arguments.

_Check the [circuit builder](../../circuit-builder/index.md) on how to generate a circuit._

```python
from opensquirrel import CircuitBuilder
from opensquirrel.passes.merger import SingleQubitGatesMerger
from math import pi  # not necessary for using the SingleQubitGatesMerger
```

```python
builder = CircuitBuilder(1)
for _ in range(4):
    builder.Rx(0, pi / 4)
circuit = builder.to_circuit()

circuit.merge(merger=SingleQubitGatesMerger())
```

??? example "`print(circuit)`"

    ```
    version 3.0

    qubit[1] q

    Rx(3.1415927) q[0]
    ```

The above example shows how four consecutive Rx rotations over $\pi/4$, are merged into a single Rx rotation over $\pi$.

The following example shows that the merging of single-qubit gates does not occur across multi-qubit gates,
non-unitary instructions, and control instructions.

```python
builder = CircuitBuilder(2, 2)
builder.Ry(0, pi / 2).X(0).CNOT(0, 1).H(0).X(1)
builder.barrier(1)
builder.H(0).X(1).measure(0, 0).H(0).X(1)
circuit = builder.to_circuit()

circuit.merge(merger=SingleQubitGatesMerger())
```

??? example "`print(circuit)`"

    ```
    version 3.0

    qubit[2] q
    bit[2] b

    H q[0]
    CNOT q[0], q[1]
    H q[0]
    X q[1]
    barrier q[1]
    H q[0]
    b[0] = measure q[0]
    H q[0]
    ```

!!! note

    In the above example, note that even though the `barrier` is placed on qubit at index 1,
    that the Hadamards (`H`) on qubit at index 0 on either side of that barrier are not merged.
    Barriers are unique in this regard; no merging of single-qubit gates occurs across barriers
    regardless of the qubit on which the barrier acts.

The final example below shows how the circuit depth ultimately increases,
even though the single-qubit gates where merged using the single-qubit gates merging pass.

```python
builder = CircuitBuilder(1)
builder.Rx(0, pi / 3).Ry(0, pi / 5)
circuit = builder.to_circuit()

circuit.merge(merger=SingleQubitGatesMerger())
circuit.decompose(decomposer=McKayDecomposer())
```

??? example "`print(circuit)`"

    ```
    version 3.0

    qubit[1] q

    Rz(-2.2688338) q[0]
    X90 q[0]
    Rz(1.9872376) q[0]
    X90 q[0]
    Rz(-1.2436334) q[0]
    ```
