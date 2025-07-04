Compilation passes are essential steps in the process of converting a high-level quantum algorithm (i.e. quantum
circuits) into a hardware-specific executable format.
This process, known as _quantum compilation_,
involves several stages to ensure that the quantum circuit can be executed efficiently on a given quantum hardware.

Compilation passes include various optimization techniques and transformations applied to the quantum circuit.
These passes can involve _qubit routing_, _initial mapping_, _gate decomposition_, or _error correction_.
These optimization steps are essential to the execution of quantum algorithms.
Often times, the design of quantum algorithms does not take into account the constraints or limitations imposed by the
target hardware, such as qubit coupling map or native gate set.

These passes are therefore needed to ensure that an initial circuit is converted to a version that adheres to the
requirements of the hardware. They can easily be used with various methods, via the `Circuit` object (e.g. _circuit.validate_, _circuit.decompose_, _circuit.map_).  

## Integrated passes

- Reader (cQASM parser: using libQASM)
- Writer (writes to cQASM)

## Types of passes

The following passes are available:

- [Decomposer](types-of-passes/decomposition/index.md)
- [Exporter](types-of-passes/exporting/index.md)
- [Mapper](types-of-passes/mapping/index.md)
- [Merger](types-of-passes/merging/index.md)
- [Router](types-of-passes/routing/index.md)
- [Validator](types-of-passes/validation/index.md)
