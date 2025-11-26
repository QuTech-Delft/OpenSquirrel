Instead of writing the circuit out to the [default cQASM format](https://qutech-delft.github.io/cQASM-spec/),
one can also use a custom exporter pass to export the circuit to a particular output format.

Exporting can be done by calling the `export` method on the circuit object and providing the desired exporter
`exporter` as an input argument to the call, _e.g._,

!!! example ""

    ```python
    from opensquirrel import CQasmV1Exporter

    exported_circuit = circuit.export(exporter=CQasmV1Exporter)
    ```

As shown in the example above, the exported circuit is given as the return value.

The following exporting passes are available in OpenSquirrel:

- [cQASMv1 exporter](cqasm-v1-exporter.md) (`CQasmV1Exporter`)
- [quantify-scheduler exporter](quantify-scheduler-exporter.md) (`QuantifySchedulerExporter`)

!!! warning "Unsupported language features"

    Note that certain features of the [cQASM language](https://qutech-delft.github.io/cQASM-spec/) may not be supported
    by the language to which the circuit is exported.
    These features are either processed by the exporter (_e.g._ control instructions),
    an error is raised, or some features will simply be lost/ignored and lose their intended effect.
    Especially, certain gates may not have a counterpart in the language that is exported to
    _e.g._ the general `Rn` gate.
    One could circumvent this latter issue by decomposing the circuit into gates that are supported.
    Make sure to consult the documentation on the particular exporters to understand the exporting process and result.
