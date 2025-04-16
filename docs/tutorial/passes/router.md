# Router Passes

The qubit routing pass is a crucial step in the process of quantum compilation. It involves transforming quantum circuits to ensure that all two-qubit operations comply with the connectivity constraints of a target quantum hardware architecture.

In quantum computing, qubits are often arranged in specific topologies where only certain pairs of qubits can directly interact. The routing pass adjusts the initial mapping of virtual qubits to physical qubits by inserting necessary operations, such as _SWAP_ gates, to move qubits into positions where they can interact as required by the quantum circuit. This process is essential because it ensures that the quantum circuit can be executed on the hardware without violating its connectivity constraints.

# Routing Passes

_OpenSquirrel_ faciliates the following routing passes.

## Shortest-Path Routing

Within this routing pass, SWAP gates are introduced along the shortest path between qubit pairs that need to interact on the hardware, but do not share a connection. While simple and straight-forward, this may result in an overly increased circuit depth. 

### Class Object

```python
ShortestPathRouter(connectivity: dict[str, list[int]])
```

### Attribute(s)

```python
connectivity: dictionary where key-values pairs represent 
qubit connections on the backend.
```

### Method(s)

```python
def route(self, ir: IR) -> IR:
    """
    Routes the circuit by inserting SWAP gates along the shortest path between qubits which can not  # noqa: W291
    interact with each other, to make it executable given the hardware connectivity.
    Args:
        ir: The intermediate representation of the circuit.
    Returns:
        The intermediate representation of the routed circuit (including the additional SWAP gates).
    """
```

## A* Routing

The A* qubit routing algorithm uses the A* search algorithm to find the optimal path between qubits that need to interact but are not directly connected on the hardware. By leveraging simple heuristics such as Manhattan, Euclidean, or Chebyshev distances, it balances the trade-off between circuit depth and computational efficiency. This approach ensures that SWAP gates are inserted along the most efficient paths, minimizing the overall cost of routing while adhering to the hardware's connectivity constraints.

### Class Object

```python
AStarRouter(connectivity: dict[str, list[int]], distance_metric: DistanceMetric = None) 
```

### Attribute(s)

```python
connectivity: dictionary where key-values pairs represent 
qubit connections on the backend.
distance_metric: metric to use in the computation of the shortest path
between two nodes
```

### Method(s)

```python
def route(self, ir: IR) -> IR:
    """
    Routes the circuit by inserting SWAP gates, with A*, to make it executable given the hardware connectivity.
    Args:
        ir: The intermediate representation of the circuit.
    Returns:
        The intermediate representation of the routed circuit (including the additional SWAP gates).
    """
```

## QRoute 

T.B.I.