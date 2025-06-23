# OpenSquirrel

This site contains the documentation for OpenSquirrel, _i.e._, a flexible quantum program compiler.
OpenSquirrel chooses a _modular_, over a _configurable_, approach to prepare and optimize quantum circuits for
heterogeneous target architectures.

It has a user-friendly interface and is straightforwardly extensible with custom-made readers,
compiler passes, and exporters.
As a quantum circuit compiler, it is fully aware of the semantics of each gate and arbitrary quantum gates can be
constructed manually.
It understands the quantum programming language cQASM 3 and will support additional quantum programming languages in the
future.
It is developed in modern Python and follows best practices.

\[[GitHub repository](<https://github.com/QuTech-Delft/OpenSquirrel>)\]
\[[PyPI](<https://pypi.org/project/opensquirrel/>)\]

## Table of Contents

- [Tutorial](tutorial/index.md)
- [Circuit builder](circuit-builder/index.md)
- [Compilation passes](compilation-passes/index.md)

[//]: # (- [API documentation]&#40;reference/reference.md&#41;)

## Authors

Quantum Inspire (<support@quantum-inspire.com>)

## Acknowledgements

The Quantum Inspire project (by QuTech: a collaboration of TNO and TU Delft)
