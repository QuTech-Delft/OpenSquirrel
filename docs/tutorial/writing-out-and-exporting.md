As you have seen in the examples above, you can turn a circuit into a
[cQASM](https://qutech-delft.github.io/cQASM-spec) string
by simply using the `str` or `__repr__` methods.
We are aiming to support the possibility to export to other languages as well,
_e.g._, a OpenQASM 3.0 string, and frameworks, _e.g._, a Qiskit quantum circuit.

Note that you can only export if the gates/instructions/statements in the compiled circuit have representations in the
exporter.
