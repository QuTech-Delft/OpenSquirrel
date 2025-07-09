Within this routing pass, SWAP gates are introduced along the shortest path between qubit pairs that need to interact on
the hardware, but do not share a connection.
While simple and straight-forward, this may result in an overly increased circuit depth.

The [ShortestPathRouter](http://127.0.0.1:8000/reference/passes/router/shortest_path_router.html) pass is a compilation step that ensures all two-qubit gates in a circuit can be 
executed on a given hardware topology. When a two-qubit gate involves qubits that are not directly connected on the device, 
this pass finds the shortest path between them using the hardware’s connectivity graph. It then inserts the necessary SWAP gates along this path, 
moving the qubits closer together so the intended operation can be performed. This approach aims to minimize the number of SWAPs required for each interaction 
by using the shortest path method from the _networkx_ package.

The following examples showcase the usage of the `ShortestPathRouter` pass.
Check the [circuit builder](../../../circuit-builder/index.md) on how to generate the circuit.

```python
from opensquirrel import CircuitBuilder
from opensquirrel.passes.router import ShortestPathRouter

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

num_swaps_inserted = sum(1 for statement in circuit.ir.statements if isinstance(statement, SWAP))
print(num_swaps_inserted)
```

_Output_:

    4

```python
from opensquirrel import CircuitBuilder
from opensquirrel.passes.router import ShortestPathRouter

connectivity = {"0": [1, 2], "1": [0, 3], "2": [0, 4], "3": [1, 5], "4": [2, 5], "5": [3, 4, 6], "6": [5]}

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

num_swaps_inserted = sum(1 for statement in circuit.ir.statements if isinstance(statement, SWAP))
print(num_swaps_inserted)
```

_Output_:

    8