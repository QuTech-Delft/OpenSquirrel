This pass checks whether all the connections outlined in the description of the quantum algorithm (i.e. qubits which need to interact because of various 2-qubit gates) are executable on the hardware. If there certain connections which are not possible on the hardware, the validator will throw a `ValueError`, specifying which qubit interactions prevent the execution.

## Class Object

```python
RoutingValidator(connectivity: dict[str, list[int]])
```

### Attribute(s)

```python
connectivity: dictionary where key-values pairs represent
qubit connections on the backend.
```

## Example

The `RoutingValidator` can be used in the following manner to check whether all qubit interactions defined in the quantum algorithm are available in the circuit.

```python
from opensquirrel import CircuitBuilder
from opensquirrel.circuit import Circuit
from opensquirrel.passes.validator import RoutingValidator

connectivity = {"0": [1, 2], "1": [0, 2, 3], "2": [0, 1, 4], "3": [1, 4], "4": [2, 3]}

validator = RoutingValidator(connectivity = connectivity)

builder = CircuitBuilder(5)
builder.H(0)
builder.CNOT(0, 1)
builder.H(2)
builder.CNOT(1, 2)
builder.CNOT(2, 4)
builder.CNOT(3, 4)
circuit = builder.to_circuit()

validator.validate(circuit.ir)
```

In the scenario above, there will be no output, as all qubit connections are executable. On the other hand, the script below will raise a `ValueError` (considering the same `validator` object and `connectivity` as above).

```python
builder = CircuitBuilder(5)
builder.H(0)
builder.CNOT(0, 1)
builder.CNOT(0, 3)
builder.H(2)
builder.CNOT(1, 2)
builder.CNOT(1, 3)
builder.CNOT(2, 3)
builder.CNOT(3, 4)
builder.CNOT(0, 4)

validator.validate(circuit.ir)
```
_Output_:

    ValueError: the following qubit interactions in the circuit prevent a 1-to-1 mapping: [(0, 3), (2, 3), (0, 4)]
