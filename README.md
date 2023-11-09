### Mini-compiler for Quantum Inspire's quantum chip[munks]

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

# Installation

## General installation

```shell
$ pip install opensquirrel
```

## Editable installation

Run the following command in the root directory of `OpenSquirrel`
```shell
$ pip install -e .
```

To install the developer specific dependencies, run the command
```shell
$ pip install -e '.[dev]'
```

# Documentation

The package exposes only the `Circuit` class, whose up-to-date documentation is accessed:

- from the Python console:
```pycon
>>> import opensquirrel
>>> help(opensquirrel.Circuit)
```

- from a Linux shell: `python3 -c "import opensquirrel; help(opensquirrel.Circuit)"`

Currently there is also a set of default gates exposed as `opensquirrel.DefaultGates` to use in the `Circuit` constructor.