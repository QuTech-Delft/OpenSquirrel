The qubit routing pass is a crucial step in the process of quantum compilation.
It involves transforming quantum circuits to ensure that all two-qubit operations comply with the connectivity
constraints of a target quantum hardware architecture.

In quantum computing, qubits are often arranged in specific topologies where only certain pairs of qubits can directly
interact.
The routing pass adjusts the initial mapping of virtual qubits to physical qubits by inserting necessary operations,
such as _SWAP_ gates, to move qubits into positions where they can interact as required by the quantum circuit.
This process is essential because it ensures that the quantum circuit can be executed on the hardware without violating
its connectivity constraints.

The following routing passes are available in _Opensquirrel_:

- [Shortest Path Router](shortest-path-router.md)

- [A* Router](a-star-router.md)
