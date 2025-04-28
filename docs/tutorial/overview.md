# Installation

_OpenSquirrel_ is available through the Python Package Index ([PyPI](<https://pypi.org/project/opensquirrel/>)).

Accordingly, installation is as easy as ABC:
```shell
$ pip install opensquirrel
```

You can check if the package is installed by importing it:
```python
import opensquirrel
```

# Creating a circuit

OpenSquirrel's entrypoint is the `Circuit` object, which represents a quantum circuit.
You can create a circuit in two different ways:

1. From a [cQASM string](creating-a-circuit/from-a-cqasm-string.md)
2. By using the [`CircuitBuilder`](creating-a-circuit/using-the-circuit-builder.md) in Python.

The _cQASM_ documentation can be found by clicking on [this link](https://qutech-delft.github.io/cQASM-spec).


When building quantum circuits, it is important to keep in mind that the quantum gates defined in _OpenSquirrel_ are subject to [strong typing](creating-a-circuit/strong-types.md) requirements.

# Modifying a circuit

There are various ways in which the design of a circuit can be tailored to meet specific needs.

1. [Merging Single Qubit Gates](applying-compilation-passes/merging-single.md)
2. [Custom Quantum Gates](applying-compilation-passes/custom-gates.md)

## Gate Decomposition

OpenSquirrel can also _decompose_ the gates of a quantum circuit, given a specific decomposition.
The package offers several, so-called, decomposers out of the box,
but users can also make their own decomposer and apply them to the circuit.
Decompositions can be:

1. [Predefined](applying-compilation-passes/decomposition/predefined.md)
2. [Inferred](applying-compilation-passes/decomposition/inferred.md) from the gate semantics.

# Exporting a circuit

As you have seen in the examples above, you can turn a circuit into a
[cQASM](https://qutech-delft.github.io/cQASM-spec) string
by simply using the `str` or `__repr__` methods.
We are aiming to support the possibility to export to other languages as well,
_e.g._, a OpenQASM 3.0 string, and frameworks, _e.g._, a Qiskit quantum circuit.

# Compilation Passes

OpenSquirrel has several ready to use, out of the box compilation passes, meant to perform necessary modifications to the quantum circuit and faciliate its execution on a quantum computer.

These compilation passes include the following:

1. [Decomposer](../compilation-passes/passes/decomposers/decomposers.md)
2. [Exporters](../compilation-passes/passes/exporters/exporters.md)
2. [Mapper](../compilation-passes/passes/mappers/mappers.md)
3. [Router](../compilation-passes/passes/routers/routers.md)
4. [Validator](../compilation-passes/passes/validators/validators.md)
5. [Merger](../compilation-passes/passes/mergers/mergers.md)



