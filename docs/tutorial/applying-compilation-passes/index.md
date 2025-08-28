There are various ways in which the design of a circuit can be tailored to meet specific needs.

1. [Merging Single Qubit Gates](../applying-compilation-passes/merging-single-qubit-gates.md)
2. [Custom Quantum Gates](../applying-compilation-passes/custom-gates.md)

## Gate Decomposition

OpenSquirrel can also _decompose_ the gates of a quantum circuit, given a specific decomposition.
The package offers several, so-called, decomposers out of the box,
but users can also make their own decomposer and apply them to the circuit.
Decompositions can be:

1. [Predefined](../applying-compilation-passes/decomposition/predefined-decomposition.md)
2. [Inferred](../applying-compilation-passes/decomposition/inferred-decomposition.md) from the gate semantics.

## Exporting a circuit

As you have seen in the examples above, you can turn a circuit into a
[cQASM](https://qutech-delft.github.io/cQASM-spec) string
by simply using the `str` or `__repr__` methods.
We are aiming to support the possibility to export to other languages as well,
_e.g._, a OpenQASM 3.0 string, and frameworks, _e.g._, a Qiskit quantum circuit.

## Compilation Passes

OpenSquirrel has several ready to use, out of the box compilation passes, meant to perform necessary modifications to
the quantum circuit and facilitate its execution on a quantum computer.

These compilation passes include the following:

1. [Decomposition](../../compilation-passes/types-of-passes/decomposition/index.md)
2. [Exporting](../../compilation-passes/types-of-passes/exporting/index.md)
3. [Mapping](../../compilation-passes/types-of-passes/mapping/index.md)
4. [Merging](../../compilation-passes/types-of-passes/merging/index.md)
5. [Routing](../../compilation-passes/types-of-passes/routing/index.md)
6. [Validation](../../compilation-passes/types-of-passes/validation/index.md)
