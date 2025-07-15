The shortest-path routing pass (`ShortestPathRouter`) ensures that qubit interactions in a circuit can be executed
given the target backend connectivity.
It inserts the necessary SWAP gates along the shortest path,
moving the qubits closer together so the intended operation can be performed.
This approach aims to minimize the number of SWAPs required for each interaction
by using the `shortest_path` method from the `networkx` package.
While it uses a straightforward algorithm, it may result in an overly increased circuit depth.

The following examples showcase the usage of the shortest-path routing pass.
Note that the backend connectivity is required as an input argument.

_Check the [circuit builder](../../circuit-builder/index.md) on how to generate the circuit._

```python
from opensquirrel import CircuitBuilder
from opensquirrel.passes.router import ShortestPathRouter
```

```python
connectivity = {"0": [1], "1": [0, 2], "2": [1, 3], "3": [2, 4], "4": [3]}

builder = CircuitBuilder(5)
builder.CNOT(0, 1)
builder.CNOT(1, 2)
builder.CNOT(2, 3)
builder.CNOT(3, 4)
builder.CNOT(0, 4)
circuit = builder.to_circuit()

shortest_path_router = ShortestPathRouter(connectivity=connectivity)
circuit.route(router=shortest_path_router)
```

??? example "`print(circuit)`"

    ```
    version 3.0

    qubit[5] q

    CNOT q[0], q[1]
    CNOT q[1], q[2]
    CNOT q[2], q[3]
    CNOT q[3], q[4]
    SWAP q[0], q[1]
    SWAP q[1], q[2]
    SWAP q[2], q[3]
    CNOT q[3], q[4]
    ```

```python
connectivity = {
    "0": [1, 2],
    "1": [0, 3],
    "2": [0, 4],
    "3": [1, 5],
    "4": [2, 5],
    "5": [3, 4, 6],
    "6": [5]
}

builder = CircuitBuilder(7)
builder.CNOT(0, 6)
builder.CNOT(1, 5)
builder.CNOT(2, 4)
builder.CNOT(3, 6)
builder.CNOT(0, 2)
builder.CNOT(1, 3)
builder.CNOT(4, 5)
builder.CNOT(5, 6)
circuit = builder.to_circuit()

shortest_path_router = ShortestPathRouter(connectivity=connectivity)
circuit.route(router=shortest_path_router)
```

??? example "`print(circuit)`"

    ```
    version 3.0

    qubit[7] q

    SWAP q[0], q[1]
    SWAP q[1], q[3]
    SWAP q[3], q[5]
    CNOT q[5], q[6]
    SWAP q[0], q[1]
    CNOT q[1], q[5]
    CNOT q[2], q[4]
    SWAP q[0], q[1]
    SWAP q[1], q[3]
    SWAP q[3], q[5]
    CNOT q[5], q[6]
    SWAP q[3], q[1]
    SWAP q[1], q[0]
    CNOT q[0], q[2]
    SWAP q[1], q[3]
    CNOT q[3], q[3]
    SWAP q[4], q[2]
    SWAP q[2], q[0]
    CNOT q[0], q[5]
    SWAP q[1], q[3]
    SWAP q[3], q[5]
    CNOT q[5], q[6]
    ```

If, based on the connectivity, a certain interaction is not possible, the shortest-path router will throw an error;
as shown in the following example where qubits 0 and 1 are disconnected from qubits 2 and 3.

```python
connectivity = {"0": [1], "1": [0], "2": [3], "3": [2]}

builder = CircuitBuilder(4)
builder.CNOT(0, 2)
builder.CNOT(3, 1)
circuit = builder.to_circuit()

shortest_path_router = ShortestPathRouter(connectivity=connectivity)
circuit.route(router=shortest_path_router)
```

!!! example ""

    `NoRoutingPathError: No routing path available between qubit 0 and qubit 2`
