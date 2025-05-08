The A* qubit routing algorithm uses the A* search algorithm to find the optimal path between qubits that need to
interact but are not directly connected on the hardware.
By leveraging simple heuristics such as Manhattan, Euclidean, or Chebyshev distances,
it balances the trade-off between circuit depth and computational efficiency.
This approach ensures that SWAP gates are inserted along the most efficient paths,
minimizing the overall cost of routing while adhering to the hardware's connectivity constraints.

## Class Object

```python
AStarRouter(connectivity: dict[str, list[int]], distance_metric: DistanceMetric = None)
```

## Attribute(s)

```python
connectivity: dictionary where key-values pairs represent
qubit connections on the backend.
distance_metric: metric to use in the computation of the shortest path
between two nodes
```

## Method(s)

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
