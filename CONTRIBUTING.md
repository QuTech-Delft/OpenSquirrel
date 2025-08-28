We recommend working on a feature branch and pull request from there.

## Requirements

- `uv`,
- `PyCharm` (recommended).

## Creating a feature branch

Make sure your environment contains all the updated versions of the dependencies.

From an OpenSquirrel checkout:

```
$ uv sync
```

And that you base your feature branch off an updated `develop`.

```
$ git checkout develop
$ git fetch origin
$ git pull
$ git branch <feature branch name>
```

## Before creating the pull request

Make sure the tests and the following linters pass.
Using `tox` (started from an OpenSquirrel checkout):

```
$ tox -e fix,type,test
```

## Setting the Python interpreter (PyCharm)

You can choose the Python interpreter from the `uv` environment.

- Go to `Settings` > `Project: OpenSquirrel` > `Python Interpreter`.
- Click on `Add Interpeter`, and then select `Add Local Interpreter`.
- Select `uv Environment`, and then `Existing environment`.
- Click on `...` to navigate to the `Interpreter` binary.

## Running/Debugging tests (PyCharm)

To run/debug all tests:

- Right-click on the `tests` folder of the Project tree.
- Click `Run 'pytest' in tests` or `Debug 'pytest' in tests`.

This will also create a `Run/Debug Configuration`.

### Troubleshooting

If breakpoints are not hit during debugging:

- Go to `Run/Debug Configurations`.
- Add `--no-cov` in the `Additional arguments` text box.

This issue may be due to the code coverage module _hijacking_ the tracing mechanism
(check [this link](https://stackoverflow.com/a/56235965/260313) for a more detailed explanation).
