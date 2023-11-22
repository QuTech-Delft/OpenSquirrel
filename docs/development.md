## Development

### Tools

**TODO**: Describe use of the devcontainer (PyCharm, VS Code)

#### Poetry

Project dependencies are specified in the `pyproject.toml` file in the root directory of the project.

Website: <https://python-poetry.org/>



Install dependencies

```shell
$ poetry install
```

Start a Poetry shell

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

##### MkDocs

The documentation is generated using MkDocs. For full documentation visit [mkdocs.org](https://www.mkdocs.org).

    mkdocs.yml    # The configuration file.
    docs/
        index.md  # The documentation homepage.
        ...       # Other markdown pages, images and other files.

##### Commands

* `mkdocs new [dir-name]` - Create a new project.
* `mkdocs serve` - Start the live-reloading docs server.
* `mkdocs build` - Build the documentation site.
* `mkdocs -h` - Print help message and exit.

#### MyPy

Check Python typing by running the following command in the root directory



