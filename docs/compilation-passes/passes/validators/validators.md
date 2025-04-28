# Validator Passes

The _Validator_ passes in OpenSquirrel are meant to provide some tools to check whether a quantum circuit is executable given the restraints imposed by the hardware.

_OpenSquirrel_ faciliates the following validator passes.

## Routing Validator

This pass checks whether all the connections outlined in the description of the quantum algorithm (i.e. qubits which need to interact because of various 2-qubit gates) are executable on the hardware. If there certain connections which are not possible on the hardware, the validator will throw a `ValueError`, specifying which qubit interactions prevent the execution.

### Class Object

```python
RoutingValidator(connectivity: dict[str, list[int]])
```

### Attribute(s)

```python
connectivity: dictionary where key-values pairs represent 
qubit connections on the backend.
```

### Example

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

## Native Gate Validator

When developing quantum algorithms, their compilation on a specific device depends on whether the hardware supports the operations implemented on the circuit. To this end, the native gate validator pass checks whether the quantum gates on the quantum circuit are present in the native gate set of the quantum hardware. If this is not the case, the validator will throw a `ValueError`, specifying which gates are present in the circuit's description, but not in the hardware's native gate set. 

### Class Object 

```python
NativeGateValidator(native_gate_set: list[str])
```

### Attribute(s)

```python
native_gate_set: A list containing the native gate set.
```

The `NativeGateValidator` can be used as such.

```python
from opensquirrel import CircuitBuilder
from opensquirrel.circuit import Circuit
from opensquirrel.passes.validator import NativeGateValidator

native_gate_set = ["I", "X90", "mX90", "Y90", "mY90", "Rz", "CZ"]

validator = NativeGateValidator(native_gate_set = native_gate_set)

builder = CircuitBuilder(5)
builder.I(0)
builder.X90(1)
builder.mX90(2)
builder.Y90(3)
builder.mY90(4)
builder.Rz(0, 2)
builder.CZ(1, 2)
builder.H(0)
builder.CNOT(1, 2)
circuit = builder.to_circuit()

validator.validate(circuit.ir)
```
_Output_:

    ValueError: the following gates are not in the native gate set: ['H', 'CNOT']

