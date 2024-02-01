# Mini-compiler for Quantum Inspire's quantum chip(munk)s

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

## Installation

```shell
$ pip install opensquirrel
```

### Editable installation

To perform an editable install, run the following command in the root directory of `OpenSquirrel` with the `-e` flag:

```shell
$ pip install -e .
```

To install the developer specific dependencies, run the command:

```shell
$ pip install -e '.[dev]'
```

## Documentation

OpenSquirrel documentation is hosted through GitHub Pages [here](https://QuTech-Delft.github.io/OpenSquirrel/).

### MkDocs

The documentation is generated using MkDocs. For full documentation visit [mkdocs.org](https://www.mkdocs.org).

    mkdocs.yml    # The configuration file.
    docs/
        index.md  # The documentation homepage.
        ...       # Other markdown pages, images and other files.

In order to build `OpenSquirrel` documentation, run the following command in the root directory of `OpenSquirrel`:

```shell
mkdocs build
```

### Style guide

We use the [Google style guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) for the docstring format.

## Tools

### Poetry

Project dependencies are specified in the `pyproject.toml` file in the root directory of the project.

Website: <https://python-poetry.org/>

Install dependencies:

```shell
$ poetry install
```

Start a Poetry shell:

```shell
$ poetry shell
```

Within the shell PyTest and MyPy can be run accordingly:

```shell
$ mypy -p opensquirrel
```

```shell
$ pytest
```
