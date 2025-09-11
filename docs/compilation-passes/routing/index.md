The qubit routing pass is a crucial step in the process of quantum compilation.
It ensures that two-qubit interactions can be executed given a certain target backend.

On quantum processing units (QPUs) qubits are often arranged in specific topologies where only certain pairs of qubits
can directly interact.
Which qubits can interact is given by a mapping called the backend connectivity, _e.g._:

=== "Linear"

    ```python
    connectivity = {
        "0": [1],
        "1": [0, 2],
        "2": [1, 3],
        "3": [2, 4],
        "4": [3]
    }
    ```

=== "Star-shaped"

    ```python
    connectivity = {
        "0": [2],
        "1": [2],
        "2": [0, 1, 3, 4],
        "3": [2],
        "4": [2]
    }
    ```

=== "Diamond-shaped"

    ```python
    connectivity = {
        "0": [1, 2],
        "1": [0, 3, 4],
        "2": [0, 4, 5],
        "3": [1, 4, 6],
        "4": [1, 2, 6, 7],
        "5": [2, 4, 7],
        "6": [3, 4, 8],
        "7": [4, 5, 8],
        "8": [6, 7],
    }
    ```

The routing pass modifies the quantum circuit by inserting operations—typically _SWAP_ gates—
that distribute the qubits such that the defined interactions can take place between connected qubits.
In other words, it ensures that all qubit interactions respect the connectivity constraints,
making the circuit executable on the target backend.

The following routing passes are available in Opensquirrel:

- [A* router](a-star-router.md) (`AStarRouter`)
- [Shortest-path router](shortest-path-router.md) (`ShortestPathRouter`)
