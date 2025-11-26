## Writing out

OpenSquirrel's native tongue is
[cQASM](https://qutech-delft.github.io/cQASM-spec/).
Accordingly, it is straightforward to write out a circuit, since the string representation of a circuit is a cQASM
string.

Use the Python built-in methods `str` or `print` to obtain the cQASM string of the circuit.

In the case of the example program that we compiled in the [previous section](applying-compilation-passes.md),
we simply do the following to write out the circuit:

```python
# To return the cQASM string
cqasm_string = str(circuit)

# To print the cQASM string
print(circuit)
```

## Exporting

Alternatively, it is possible to [export](../compilation-passes/exporting/index.md) the circuit to a
different format.
This can be done by using the `export` method with the desired format as an input argument.

For instance, if we want to export our circuit to
[cQASM 1.0](https://libqasm.readthedocs.io/) (given by the export format `CQASM_V1`) we write the following:

```python
from opensquirrel.passes.exporter import CqasmV1Exporter

exported_circuit = circuit.export(exporter=CqasmV1Exporter())
```

This uses the [cQASMv1 exporter](../compilation-passes/exporting/cqasm-v1-exporter.md) to export the
circuit to a cQASM 1.0 string.

??? example "`print(exported_circuit)  # Compiled program in terms of cQASM 1.0`"

    ```linenums="1"
    version 1.0

    qubits 3

    prep_z q[0]
    prep_z q[1]
    prep_z q[2]
    rz q[0], 1.5707963
    x90 q[0]
    rz q[0], 1.5707963
    rz q[1], 1.5707963
    x90 q[1]
    rz q[1], -1.5707963
    cz q[0], q[1]
    rz q[1], -1.5707963
    x90 q[1]
    rz q[1], 1.5707963
    rz q[0], 1.5707963
    x90 q[0]
    rz q[0], -1.5707963
    cz q[1], q[0]
    rz q[0], -1.5707963
    x90 q[0]
    rz q[0], 1.5707963
    rz q[1], 1.5707963
    x90 q[1]
    rz q[1], -1.5707963
    cz q[0], q[1]
    rz q[1], -1.5707963
    x90 q[1]
    rz q[1], 1.5707963
    rz q[2], 1.5707963
    x90 q[2]
    rz q[2], -1.5707963
    cz q[1], q[2]
    rz q[2], -1.5707963
    x90 q[2]
    rz q[2], 1.5707963
    barrier q[1, 0, 2]
    measure_z q[1]
    measure_z q[2]
    ```

Note that there may be language constructs that do not have a straightforward translation from cQASM to the chosen
format. For example, [cQASM 1.0](https://libqasm.readthedocs.io/) does not support the declaration of bit registers.
Consequently, any information regarding bit registers and variables will be _lost-in-translation_, _e.g._,
in cQASM 1.0, measurement outcomes cannot be written to a specific bit register variable even if this has been done in
the original cQASM program.

!!! warning "Translation is not always straightforward"

    Make sure to check the documentation on the specific
    [exporters](../compilation-passes/exporting/index.md) to understand how the translation is done,
    since not all language constructs can be straightforwardly translated from
    [cQASM](https://qutech-delft.github.io/cQASM-spec/) into any alternative format.
