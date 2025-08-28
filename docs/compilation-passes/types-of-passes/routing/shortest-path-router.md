Within this routing pass, SWAP gates are introduced along the shortest path between qubit pairs that need to interact on
the hardware, but do not share a connection.
While simple and straight-forward, this may result in an overly increased circuit depth.

## Class Object

```python
ShortestPathRouter(connectivity: dict[str, list[int]])
```

## Attribute(s)

```python
connectivity: dictionary where key-values pairs represent
qubit connections on the backend.
```

## Method(s)

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
