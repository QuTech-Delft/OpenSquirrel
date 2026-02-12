Contributing to OpenSquirrel largely follows the general procedure of
[contributing to a GitHub project](https://docs.github.com/en/get-started/exploring-projects-on-github/contributing-to-a-project).
Some details of that procedure and actions specific to OpenSquirrel are described below.

## Requirements

- [git](https://github.com/git-guides) version control system (VCS) for software programming:
  [Install Git](https://github.com/git-guides/install-git) and check if it is installed properly by running 
  `git version`.
- [uv](https://docs.astral.sh/uv/) Python package manager: easy install through `pip install uv` or follow
[these instructions](https://docs.astral.sh/uv/getting-started/installation/).

## Forking the project and creating a feature branch

Contributing to OpenSquirrel as an external developer is done via a new fork.

- Navigate to the [OpenSquirrel GitHub project](https://github.com/QuTech-Delft/OpenSquirrel)
and create a [fork](https://docs.github.com/en/get-started/exploring-projects-on-github/contributing-to-a-project#creating-your-own-copy-of-a-project).
- Clone the repository locally using `git clone`.
- Create a new feature branch:
  ```bash
  git checkout develop
  git fetch origin
  git pull
  git branch <name-feature-branch>
  ```

## Installing the required dependencies

It is recommended to work in a virtual environment (which can be created using `uv`)
```
uv venv <name-of-venv>
```

Make sure to activate the virtual environment if not done so yet

=== "Windows"
    ```powershell
    .\<name-of-venv>\Scripts\activate
    ```

=== "Linux/MacOS"
    ```bash
    source <name-of-venv>/bin/activate
    ```

Next install the required dependencies 
```
uv sync
```

## Adding, committing, and pushing changes

Any code changes can be added as follows
```bash
git add <name-of-file-or-directory-with-changes>
```
Use `git status` to inspect which files contain changes and which of them have already been _staged_, _i.e._, added.

To _save_ the changes in the staged files, you create so-called commit, accordingly
```bash
git commit -m "<commit-message>"
```
where the commit message is a short description of the changes made.

To make sure that the changes not only exist locally, the commit needs to be pushed to the remote repository.
```bash
git push
```

## Creating a Pull Request

When you are done with your feature implementation and want to add it to OpenSquirrel, you need to
[create a Pull Request](https://docs.github.com/en/get-started/exploring-projects-on-github/contributing-to-a-project#making-a-pull-request) (PR).

Before finalizing the PR, however, it is advised to run linting, type, and unit tests, using `tox`:
```bash
pip install tox
```

```bash
tox -e fix,type,test
```

_Make sure to commit and push any changes resulting from these checks._
