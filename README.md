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

## Documentation

OpenSquirrel documentation is hosted through GitHub Pages [here](https://QuTech-Delft.github.io/OpenSquirrel/).

### MkDocs

The documentation is generated using MkDocs. For full documentation visit [mkdocs.org](https://www.mkdocs.org).

    mkdocs.yml    # The configuration file.
    docs/
        index.md  # The documentation homepage.
        ...       # Other markdown pages, images and other files.

#### Commands

* `mkdocs new [dir-name]` - Create a new project.
* `mkdocs serve` - Start the live-reloading docs server.
* `mkdocs build` - Build the documentation site.
* `mkdocs -h` - Print help message and exit.
* `mkdocs gh-deploy` - Rebuild and deploy documentation to GitHub Pages.

### Style guide

We use the [Google style guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) for the docstring format.

## Tools

### Poetry

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

## Dev Container

### PyCharm

Open the Dev Container configuration file located at `.devcontainer/devcontainer.json` in the PyCharm editor.
On the left of the editor, in the gutter, you should see the Docker icon:
<img src="docs/_static/devcontainer_docker_icon.png" width="20" height="20"> or
<img src="docs/_static/devcontainer_docker_icon_2.png" width="20" height="20">.
Upon clicking on the Docker icon, the following options appear (depending on the PyCharm version used):
**Create Dev Container and Mount Sources...** and **Show Dev Containers**.
If no Dev Containers have been created previously,
select the former option and proceed to create a Dev Container,
otherwise select the latter option to list the existing Dev Containers.

 - If you select **Create Dev Container and Mount Sources...**,
a separate window (*Building Dev Container*) will open and a Dev Container will be built according to the specification in the `devcontainer/Dockerfile`.
The system dependencies are installed, a user account (*i.e.* **pydev**) is created,
and additional Python packages and Poetry are installed.
Upon completion the status messages should read something like:
*'Dev Container' has been deployed successfully* and *Environment is successfully prepared…*
Proceed by choosing your PyCharm installation, from the dropdown menu that appears at the top, and click **Continue**.
A connection is established with the remote host and a new PyCharm window is opened.
Skip the following bullet point and proceed below.

- If you select **Show Dev Containers**,
a separate window appears where the existing (previously created) Dev Containers are listed by their name and status (*i.e.* either running or idle).
If they are idle they can be started by clicking on their name or on the play button.
Note that an idle (Dev) Container can also be started from the terminal:

    ```bash
    docker container start <container-name>
    ```

    In general, all docker containers (including idle ones) can be listed using:

    ```bash
    docker ps -a
    ```

    A running Dev Container can be accessed from the terminal, accordingly:

    ```bash
    docker exec -it <container-name> bash
    ```
Once you have accessed the Dev Container, change to the user **pydev**:

```bash
sudo -u pydev -i
```

and make sure to navigate to the project root folder:

```bash
cd /IdeaProjects/OpenSquirrel/
```

Continue to install the dependencies (if not done already in this container; otherwise you may skip this step):

```bash
poetry install
```

and initiating the Poetry shell environment:

```bash
poetry shell
```
