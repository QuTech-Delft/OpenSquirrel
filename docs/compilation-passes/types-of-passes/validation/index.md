The _Validator_ passes in _OpenSquirrel_ are meant to provide some tools to check whether a quantum circuit is
executable given the restraints imposed by the hardware.

## Routing validator

This pass checks whether all the connections outlined in the description of the quantum algorithm (i.e. qubits which
need to interact because of various 2-qubit gates) are executable on the hardware.
If there certain connections which are not possible on the hardware, the validator will throw a `ValueError`,
specifying which qubit interactions prevent the execution.

### Class Object

```python
RoutingValidator(connectivity: dict[str, list[int]])
```

### Attribute(s)

```python
connectivity: dictionary where key-values pairs represent
qubit connections on the backend.
```

### Method(s)

```python
def validate(ir: IR) -> None:
    """
    Check if the circuit interactions faciliate a 1-to-1 mapping to the target hardware.

    Args:
        ir (IR): The intermediate representation of the circuit to be checked.

    Raises:
        ValueError: If the circuit can't be mapped to the target hardware.
    """
```

## Primitive gate validator

When developing quantum algorithms, their compilation on a specific device depends on whether the hardware supports the
operations implemented on the circuit.
To this end, the primitive gate validator pass checks whether the quantum gates on the quantum circuit are present in
the primitive gate set of the quantum hardware.
If this is not the case, the validator will throw a `ValueError`,
specifying which gates are present in the circuit's description, but not in the hardware's primitive gate set.

### Class Object

```python
NativeGateValidator(native_gate_set: list[str])
```

### Attribute(s)

```python
native_gate_set: A list containing the native gate set.
```

### Method(s)

```python
def validate(ir: IR) -> None:
    """
    Check if all unitary gates in the circuit are part of the native gate set.

    Args:
        ir (IR): The intermediate representation of the circuit to be checked.

    Raises:
        ValueError: If any unitary gate in the circuit is not part of the native gate set.
    """
```
