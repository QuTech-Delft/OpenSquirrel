Compilation passes are essential steps in the process of converting a high-level quantum algorithm,
_i.e._ quantum circuits, into a hardware-specific executable format.
This process, known as _quantum compilation_,
involves several stages to ensure that the quantum circuit can be executed efficiently on a given quantum hardware.

Compilation passes include various optimization techniques and transformations applied to the quantum circuit.
These passes can involve _qubit routing_, _initial mapping_, _gate decomposition_, or _error correction_.
These optimization steps are essential to the execution of quantum algorithms.
Often times, the design of quantum algorithms does not take into account the constraints or limitations imposed by the
target hardware, such as qubit coupling map or native gate set.

These passes are therefore needed to ensure that an initial circuit is converted to a version that adheres to the
requirements of the hardware.
They can easily be applied using the following methods on the `circuit` object:

- decompose
- export
- map
- merge
- route
- validate

## Types of passes

Given the methods stated above, the following types of passes are available:

- [Decomposer](decomposition/index.md)
- [Exporter](exporting/index.md)
- [Mapper](mapping/index.md)
- [Merger](merging/index.md)
- [Router](routing/index.md)
- [Validator](validation/index.md)

!!! note "Integrated passes"

    The [reader](../tutorial/creating-a-circuit.md) and [writer](../tutorial/writing-out-and-exporting.md) passes are
    integrated in particular functionalities of the circuit.
    They are not applied in the same way as the passes mentioned above, _i.e._,
    by passing them as an argument when calling one of the aforementiond methods on the circuit.
    Instead, the reader and writer are executed when one parses a [cQASM](https://qutech-delft.github.io/cQASM-spec)
    string or writes out the circuit to a cQASM string, respectively.
    The reader is invoked when using the `Circuit.from_string` method,
    and the writer is invoked when converting the circuit to a string with `str` or printing it out with `print`.
