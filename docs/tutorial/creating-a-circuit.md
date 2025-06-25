As described in the [tutorial](index.md), a circuit can be created in two ways:

1. [from a cQASM string](creating-a-circuit.md#1-from-a-cqasm-string), or
2. [by using the circuit builder](creating-a-circuit.md#2-by-using-the-circuit-builder) in Python.

Consider the following example quantum program written in the
[cQASM language](https://qutech-delft.github.io/cQASM-spec/latest/):

!!! example ""

    ```linenums="1"

    // Version statement
    version 3.0

    // Qubit register declaration
    qubit[5] q

    // Bit register declaration
    bit[2] b

    // Qubit register initialization
    init q[0, 1]

    // Single-qubit gate
    H q[0]

    // Two-qubit gate
    CNOT q[0], q[1]

    // Control instruction
    barrier q[0, 1]

    // Measure instruction
    b[0, 1] = measure q[0, 1]

    ```

## 1. from a cQASM string

Here we demonstrate how a circuit can be created from a cQASM string,
using the `Circuit.from_string` method with the above example program as an input argument:

```python
from opensquirrel import Circuit

circuit = Circuit.from_string(
    """
    // Version statement
    version 3.0

    // Qubit register declaration
    qubit[5] q

    // Bit register declaration
    bit[2] b

    // Qubit register initialization
    init q[0, 1]

    // Single-qubit gate
    H q[0]

    // Two-qubit gate
    CNOT q[0], q[1]

    // Control instruction
    barrier q[0, 1]

    // Measure instruction
    b[0, 1] = measure q[0, 1]

    """
)
```

??? example "`print(circuit)`"

    ```
    version 3.0

    qubit[5] q
    bit[2] b

    init q[0]
    init q[1]
    H q[0]
    CNOT q[0], q[1]
    barrier q[0]
    barrier q[1]
    b[0] = measure q[0]
    b[1] = measure q[1]
    ```

The `Circuit.from_string` method invokes OpenSquirrel's reader which uses the
[libQASM parser](https://qutech-delft.github.io/libqasm/latest/) to parse the input program.

Some important things to note about how OpenSquirrel reads the input cQASM string:
the OpenSquirrel reader

- unpacks any [SGMQ notation](https://qutech-delft.github.io/cQASM-spec/latest/language_specification/statements/instructions/single-gate-multiple-qubit-notation.html)
as separate statements,
- combines all _logical_ (qu)bit registers into a single _virtual_ (qu)bit register
with identifiers `q` and `b`, signifying the qubit and bit registers, respectively, and
- ignores any [comments](https://qutech-delft.github.io/cQASM-spec/latest/language_specification/tokens/whitespace_and_comments.html);
they are simply not registered during the parsing phase.

!!! warning "OpenSquirrel's native tongue is cQASM"

    The OpenSquirrel reader only accepts quantum programs written in
    [cQASM](https://qutech-delft.github.io/cQASM-spec/latest/).
    The same applies to OpenSquirrel's writer, _i.e._,
    the string representation of a `circuit` is in cQASM.
    Nonetheless, using [exporter passes](../compilation-passes/types-of-passes/exporting/index.md) one can export to
    circuit to a different language, _e.g._,
    [quantify-scheduler Schedule](https://quantify-os.org/docs/quantify-scheduler/v0.20.1/autoapi/quantify_scheduler/index.html)
    or [cQASM 1.0](https://libqasm.readthedocs.io/en/latest/index.html).

One can now proceed to [apply compilation passes](applying-compilation-passes.md) to the `circuit` object.

## 2. by using the circuit builder

Circuits can also be defined using Python functionalities,
via the [circuit builder](../circuit-builder/index.md), as shown below.
For this, the user will first need to import the `CircuitBuilder` from `opensquirrel`.

```{ .py }
from opensquirrel import CircuitBuilder

builder = CircuitBuilder(qubit_register_size=5, bit_register_size=2)
builder.init(0).init(1)
builder.H(0)
builder.CNOT(0, 1)
builder.barrier(0).barrier(1)
builder.measure(0, 0).measure(1, 1)
circuit = builder.to_circuit()
```

??? example "`print(circuit)`"

    ```
    version 3.0

    qubit[5] q
    bit[2] b

    init q[0]
    init q[1]
    H q[0]
    CNOT q[0], q[1]
    barrier q[0]
    barrier q[1]
    b[0] = measure q[0]
    b[1] = measure q[1]
    ```

Note that the representation of the printed circuit is the same as the one obtained from the cQASM string above.

The real power of the circuit builder lies in that fact that it can be used in combination with the functionalities
available in Python to create your circuit:

```python
from opensquirrel import CircuitBuilder

qreg_size = 10
builder = CircuitBuilder(qubit_register_size=qreg_size)
for qubit_index in range(0, qreg_size, 2):
    builder.H(qubit_index)
circuit = builder.to_circuit()
```

??? example "`print(circuit)`"

    ```
    version 3.0

    qubit[10] q

    H q[0]
    H q[2]
    H q[4]
    H q[6]
    H q[8]
    ```

For instance, you can straightforwardly generate a [quantum fourier transform](https://en.wikipedia.org/wiki/Quantum_Fourier_transform) (QFT) circuit as follows:

```python
from opensquirrel import CircuitBuilder

qreg_size = 5
builder = CircuitBuilder(qubit_register_size=qreg_size)
for qubit_index in range(qreg_size):
      builder.H(qubit_index)
      for control_index in range(qubit_index + 1, qreg_size):
            target_index = qubit_index
            k = control_index - target_index + 1
            builder.CRk(control_index, target_index, k)
circuit_qft = builder.to_circuit()
```

??? example "`print(circuit_qft)`"

    ```
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
    ```

One can now proceed to [apply compilation passes](applying-compilation-passes.md) to the `circuit` object.
