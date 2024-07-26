# OpenSquirrel

[![CI](https://github.com/QuTech-Delft/OpenSquirrel/workflows/Tests/badge.svg)](https://github.com/qutech-delft/OpenSquirrel/actions)
[![PyPI](https://badgen.net/pypi/v/OpenSquirrel)](https://pypi.org/project/OpenSquirrel/)

A flexible quantum program compiler.

```
 ,;;:;,
   ;;;;;
  ,:;;:;    ,'=.
  ;:;:;' .=" ,'_\
  ':;:;,/  ,__:=@
   ';;:;  =./)_
 jgs `"=\_  )_"`
          ``'"`
```

OpenSquirrel chooses a _modular_, over a _configurable_, approach to prepare and optimize quantum circuits for heterogeneous target architectures.

It has a user-friendly interface and is straightforwardly extensible with custom-made readers, compiler passes, and exporters.
As a quantum circuit compiler, it is fully aware of the semantics of each gate and arbitrary quantum gates can be constructed manually.
It supports the cQASM quantum programming language, using [libQASM](https://github.com/QuTech-Delft/libqasm) as language parser.
It is developed in modern Python and follows best practices.

## User manual

User documentation of OpenSquirrel is hosted through [GitHub Pages](https://QuTech-Delft.github.io/OpenSquirrel/).

## File organization

For development, see:

- `opensquirrel`: source files.
- `test`: test files.

For build process, continuous integration, and documentation:

- `.github`: GitHub Actions configuration files.
- `docs`: documentation files.
- `scripts`: documentation helper script.

## Dependencies

All dependencies are managed via [poetry](https://python-poetry.org/).

From an OpenSquirrel checkout:

```shell
poetry shell
poetry install
```

## Installation

OpenSquirrel can be easily installed from PyPI.
We recommend using a virtual environment (e.g. venv).

```shell
pip install opensquirrel
```

## Usage

The `opensquirrel` module can be imported from another Python file with:

```python
import opensquirrel
```

## Licensing

OpenSquirrel is licensed under the Apache License, Version 2.0. See
[LICENSE](https://github.com/QuTech-Delft/OpenSquirrel/blob/master/LICENSE.md) for the full
license text.

## Authors

Quantum Inspire: [support@quantum-inspire.com](mailto:"support@quantum-inspire.com")
