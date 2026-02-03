# OpenSquirrel

This site contains the user documentation for OpenSquirrel, _i.e._, a compiler for gate-based quantum circuits written
in Python.
OpenSquirrel adopts a _modular_ approach to prepare and optimize circuits for heterogeneous target quantum processing
units (QPUs).

It has a user-friendly interface through its circuit builder and circuit and a collection of compilation passes,
which includes:

- [decomposition](./compilation-passes/decomposition/index.md),
- [exporting](./compilation-passes/exporting/index.md),
- [mapping](./compilation-passes/mapping/index.md),
- [merging](./compilation-passes/merging/index.md),
- [routing](./compilation-passes/routing/index.md), and
- [validation](./compilation-passes/validation/index.md).

Moreover, as OpenSquirrel 


it is straightforwardly extensible with custom-made passes.



It understands the quantum programming language cQASM 3 and will support additional quantum programming languages in the
future.
It is developed in modern Python and follows best practices.

\[[GitHub repository](<https://github.com/QuTech-Delft/OpenSquirrel>)\]
\[[PyPI](<https://pypi.org/project/opensquirrel/>)\]

## Table of Contents

### Opensquirrel

- [Installation](installation.md)
- [Contributin](contributing.md)
- [Authors](authors.md)
- [Acknowledgements](acknowledgements.md)

### User documentation

- [Tutorial](tutorial/index.md)
- [Circuit builder](circuit-builder/index.md)
- [Compilation passes](compilation-passes/index.md)
- [API documentation](reference/reference.md)

OpenSquirrel is licensed under the Apache License: version 2.0. Click 
[here](https://github.com/QuTech-Delft/OpenSquirrel/blob/develop/LICENSE.md) for the full license text.