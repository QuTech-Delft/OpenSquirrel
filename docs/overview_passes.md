# Quantum Compilation Passes

Quantum compilation passes are essential steps in the process of converting a high-level quantum algorithm (i.e. quantum circuits) into a hardware-specific executable format. This process, known as _quantum compilation_, involves several stages to ensure that the quantum circuit can be executed efficiently on a given quantum hardware.

Quantum compilation passes include various optimization techniques and transformations applied to the quantum circuit. These passes can involve _qubit routing_, _initial mapping_, _gate decomposition_, or _error correction_. These optimization steps are essential to the execution of quantum algorithms. Often times, the design of quantum algorithms does not take into account the constraints or limitations imposed by the target hardware, such as qubit coupling map or native gate set. 

These passes are therefore needed to ensure that an initial circuit is converted to a version that adheres to the requirements of the hardware. 

## Passes

The the following passes are available in _OpenSquirrel_:

1. [Decomposer](tutorial/passes/decomposer.md)
2. [Exporter](tutorial/passes/exporter.md)
3. [Mapper](tutorial/passes/mapper.md)
4. [Merger](tutorial/passes/merger.md)
5. [Router](tutorial/passes/router.md)
6. [Validator](tutorial/passes/validator.md)