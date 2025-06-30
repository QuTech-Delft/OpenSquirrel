The goal of this tutorial is to convey the basic functionalities of OpenSquirrel.
In a nutshell, we will do so by

1. [creating a circuit](creating-a-circuit.md) by reading/building a quantum program,
2. [applying compilation passes](applying-compilation-passes.md) on the circuit, and
3. [writing out and exporting](writing-out-and-exporting.md) the compiled program to various formats.

The diagram below illustrates the basic components of OpenSquirrel.
We refer to it in the following sections, where we quickly go through the 3 aforementioned steps.

<p align="center"> <img width="700" src="../../_static/overview_diagram.png"> </p>

**1. creating a circuit**

Note that on the left side of the diagram a quantum **program** written in the
[**cQASM** language](https://qutech-delft.github.io/cQASM-spec/latest/) can be read-in by the **reader**,
which uses the [libQASM parser](https://qutech-delft.github.io/libqasm/latest/) to generate the circuit.
Alternatively, a circuit can be produced by using the programmatic API of OpenSquirrel,
given by the [**circuit builder**](../circuit-builder/index.md).

Both approaches result in an instance of a `Circuit`, which comprises OpenSquirrel's main entrypoint.
The **circuit** object contains the attributes of the input quantum program
and stores its statements in an _Intermediate Representation_ (**IR**).

Check for more details: [Creating a circuit](creating-a-circuit.md)

**2. applying compilation passes**

The user can, subsequently, perform certain actions (or _methods_) on the `circuit` object;
these are (at the moment of writing and in alphabetic order):

- decompose
- export
- map
- merge
- route
- validate

For each of these actions the user will provide an appropriate [**compilation pass**](../compilation-passes/index.md)
and potential input arguments.
For instance, to obtain the
[McKay decomposition](../compilation-passes/types-of-passes/decomposition/mckay-decomposer.md) of the circuit,
one would select the `McKayDecomposer` and perform the `decompose`
action on the `circuit` object accordingly:

```python
circuit.decompose(decomposer=McKayDecomposer())
```

_This particular pass does not take any input parameters._

Each compilation pass will take the circuit or IR as input and perform the specified action on it.
Ultimately, these actions either validate or make changes to certain properties/components of the circuit,
whilst preserving the semantic content of the program.

!!! note "Order matters"

    Note that the order in which the various compilation passes are applied will have an impact on the final result.
    In particular, it will make more sense to validate a result after making any changes.
    For instance, validating wether the gates in the circuit are part of the (specified) primitive gate set,
    should be done after decomposition.

Check for more details: [Applying compilation passes](applying-compilation-passes.md)

**3. writing out or exporting the compiled program**

After the desired actions have been applied to the circuit,
one can decide to either write the compiled program to cQASM using the **writer**,
or export the result to a different format, by selecting one of the available **exporter**s.

The string representation of the `circuit` object automatically invokes the writer,
so the following line will return the (compiled) program, _i.e._ **program'** , in cQASM:

```python
str(circuit)
```
_Python's_ `print()` _statement can be used to print the program in cQASM._

If one wishes to export the (compiled) program to, for example,
a [quantify-scheduler](https://quantify-os.org/docs/quantify-scheduler/v0.24.0/) `Schedule` one would do the following,
using the [quantify-scheduler exporter](../compilation-passes/types-of-passes/exporting/quantify-scheduler-exporter.md):

```
exported_schedule, _ = circuit.export(fmt=ExportFormat.QUANTIFY_SCHEDULER)
```

Check for more details: [Writing out and exporting](writing-out-and-exporting.md)
