The [A* qubit routing pass](http://127.0.0.1:8000/reference/passes/router/astar_router.html) uses the A* search algorithm to find the optimal path between qubits that need to
interact but are not directly connected on the hardware.
By leveraging simple heuristics such as Manhattan, Euclidean, or Chebyshev distances,
it balances the trade-off between circuit depth and computational efficiency.
This approach ensures that SWAP gates are inserted along the most efficient paths,
minimizing the overall cost of routing while adhering to the hardware's connectivity constraints. 

The examples below show how this pass, along with the distance metrics, can be used to route circuits
in _OpenSquirrel_.

```python
from opensquirrel import CircuitBuilder
from opensquirrel.passes.router import AStarRouter
from opensquirrel.passes.router.heuristics import DistanceMetric

 connectivity = {"0": [1], "1": [0, 2], "2": [1, 3], "3": [2, 4], "4": [3]}

a_star_router = AStarRouter(connectivity = connectivity, distance_metric=DistanceMetric.MANHATTAN)

builder = CircuitBuilder(5)
builder.CNOT(0, 1)
builder.CNOT(1, 2)
builder.CNOT(2, 3)
builder.CNOT(3, 4)
builder.CNOT(0, 4)

circuit = builder.to_circuit()

circuit.route(router = a_star_router)
```

_Output_:

    4

```python
from opensquirrel import CircuitBuilder
from opensquirrel.passes.router import AStarRouter
from opensquirrel.passes.router.heuristics import DistanceMetric

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

a_star_router = AStarRouter(connectivity = connectivity, distance_metric=DistanceMetric.CHEBYSHEV)

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

circuit.route(router = a_star_router)
```

_Output_:

    15


