# OpenSquirrel

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
It understands the quantum programming language cQASM 3 and will support additional quantum programming languages in the future.
It is developed in modern Python and follows best practices.

## User manual

OpenSquirrel documentation is hosted through GitHub Pages [here](https://QuTech-Delft.github.io/OpenSquirrel/).

## File organization

For development, see:

- `opensquirrel`: source files.
- `test`: test files.

For build process, continuous integration, and documentation:

- `.github`: GitHub Actions configuration files.
- `docs`: documentation files.
- `scripts`: documentation helper script.

## Dependencies

All dependencies are managed via `poetry`.

From an OpenSquirrel checkout:

```shell
poetry shell
poetry install
```

## Use from another project

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
