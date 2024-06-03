We recommend to work on a feature branch and pull request from there.

## Create a feature branch

Make sure your environment contains all the updated versions of the dependencies.

```
$ poetry shell
$ poetry install
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

```
$ pytest -vv
$ mypy . --strict
$ poetry run isort .
$ poetry run black .
```
