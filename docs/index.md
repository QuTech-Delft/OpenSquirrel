# OpenSquirrel

This site contains the __User documentation__ for OpenSquirrel, _i.e._, a flexible compiler for gate-based quantum
circuits written in Python.

OpenSquirrel adopts a _modular_ approach to prepare and optimize circuits for heterogeneous target quantum processing
units (QPUs). It has a user-friendly interface through its _circuit builder_ and _circuit_ object, 
and a collection of compilation passes which includes passes for

- [decomposition](./compilation-passes/decomposition/index.md),
- [exporting](./compilation-passes/exporting/index.md),
- [mapping](./compilation-passes/mapping/index.md),
- [merging](./compilation-passes/merging/index.md),
- [routing](./compilation-passes/routing/index.md), and
- [validation](./compilation-passes/validation/index.md).

Moreover, this collection is straightforwardly extensible with custom-made passes.

The OpenSquirrel _reader_ uses the [libQASM](https://qutech-delft.github.io/libqasm/) parser
to generate the abstract syntax tree (AST) of a circuit written in the
[cQASM](https://qutech-delft.github.io/cQASM-spec/) quantum programming language. 

It is developed in modern Python and follows best practices.

\[[GitHub repository](<https://github.com/QuTech-Delft/OpenSquirrel>)\]
\[[PyPI](<https://pypi.org/project/opensquirrel/>)\]

## Table of Contents

### Opensquirrel

- [Installation](installation.md)
- [Contributing](contributing.md)
- [Authors](authors.md)
- [Acknowledgements](acknowledgements.md)

### User documentation

- [Tutorial](tutorial/index.md)
- [Circuit builder](circuit-builder/index.md)
- [Compilation passes](compilation-passes/index.md)
- [API documentation](reference/reference.md)

_OpenSquirrel is licensed under the Apache License: version 2.0. Click_
_[here](https://github.com/QuTech-Delft/OpenSquirrel/blob/develop/LICENSE.md) for the full license text._