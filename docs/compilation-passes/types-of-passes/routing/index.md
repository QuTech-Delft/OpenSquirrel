The qubit routing pass is a crucial step in the process of quantum compilation.
It involves transforming quantum circuits to ensure that all two-qubit operations comply with the connectivity
constraints of a target quantum hardware architecture.

In quantum computing, qubits are often arranged in specific topologies where only certain pairs of qubits can directly
interact.
The routing pass modifies the quantum circuit by inserting operations—typically _SWAP_ gates—that reposition qubits so 
they can interact according to the circuit’s requirements. This step ensures that all two-qubit operations respect 
the hardware’s connectivity constraints, making the circuit executable on the target device.

The following routing passes are available in _Opensquirrel_:

- [Shortest Path Router](shortest-path-router.md)
- [A* Router](a-star-router.md)
