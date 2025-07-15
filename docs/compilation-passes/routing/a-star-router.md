The A\* (pronounced _A-star_) qubit routing pass (`AStarRouter`) uses the A\* search algorithm to find the optimal path between qubits
that need to interact but are not directly connected, given the backend connectivity.
By leveraging one of the following distance metrics as a heuristic:

- Manhattan,
- Euclidean, or
- Chebyshev.

It balances the trade-off between circuit depth and computational efficiency.
This approach ensures that SWAP gates are inserted along the most efficient paths,
minimizing the overall cost of routing while adhering to the connectivity constraints.

The examples below show how the A\* qubit routing pass, along with specified distance metrics, can be used to route
circuits in OpenSquirrel, given the connectivity of the backend.

_Check the [circuit builder](../../circuit-builder/index.md) on how to generate a circuit._

```python
from opensquirrel import CircuitBuilder
from opensquirrel.passes.router import AStarRouter
from opensquirrel.passes.router.heuristics import DistanceMetric
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

a_star_router = AStarRouter(
    connectivity=connectivity,
    distance_metric=DistanceMetric.MANHATTAN
)
circuit.route(router=a_star_router)
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
        "0": [1, 2, 5],
        "1": [0, 3, 6],
        "2": [0, 4, 7],
        "3": [1, 5, 8],
        "4": [2, 6, 9],
        "5": [0, 3, 7],
        "6": [1, 4, 8],
        "7": [2, 5, 9],
        "8": [3, 6, 9],
        "9": [4, 7, 8],
}

builder = CircuitBuilder(10)
builder.CNOT(0, 9)
builder.CNOT(1, 8)
builder.CNOT(2, 7)
builder.CNOT(3, 6)
builder.CNOT(4, 5)
builder.CNOT(0, 2)
builder.CNOT(1, 3)
builder.CNOT(4, 6)
builder.CNOT(5, 7)
builder.CNOT(8, 9)
builder.CNOT(0, 5)
builder.CNOT(1, 6)
builder.CNOT(2, 8)
builder.CNOT(3, 9)
circuit = builder.to_circuit()

a_star_router = AStarRouter(
    connectivity=connectivity,
    distance_metric=DistanceMetric.CHEBYSHEV
)
circuit.route(router=a_star_router)
```

??? example "`print(circuit)`"

    ```
    version 3.0

    qubit[10] q

    SWAP q[0], q[2]
    SWAP q[2], q[4]
    CNOT q[4], q[9]
    SWAP q[1], q[6]
    CNOT q[6], q[8]
    SWAP q[0], q[2]
    CNOT q[2], q[7]
    CNOT q[3], q[6]
    CNOT q[0], q[5]
    CNOT q[4], q[2]
    SWAP q[6], q[1]
    CNOT q[1], q[3]
    SWAP q[0], q[1]
    CNOT q[1], q[6]
    CNOT q[5], q[7]
    CNOT q[8], q[9]
    SWAP q[4], q[2]
    SWAP q[2], q[0]
    CNOT q[0], q[5]
    SWAP q[2], q[4]
    CNOT q[4], q[6]
    SWAP q[2], q[4]
    SWAP q[4], q[9]
    CNOT q[9], q[8]
    SWAP q[3], q[8]
    SWAP q[8], q[9]
    CNOT q[9], q[9]
    ```

If, based on the connectivity, a certain interaction is not possible, the A\* router will throw an error;
as shown in the following example where qubits 0 and 1 are disconnected from qubits 2 and 3.

```python
connectivity = {"0": [1], "1": [0], "2": [3], "3": [2]}

builder = CircuitBuilder(4)
builder.CNOT(0, 2)
builder.CNOT(3, 1)
circuit = builder.to_circuit()

a_star_router = AStarRouter(
    connectivity=connectivity,
    distance_metric=DistanceMetric.EUCLIDEAN
)
circuit.route(router=a_star_router)
```

!!! example ""

    `NoRoutingPathError: No routing path available between qubit 0 and qubit 2`
