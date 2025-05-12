When developing quantum algorithms, their compilation on a specific device depends on whether the hardware supports the
operations implemented on the circuit.
To this end, the native gate validator pass checks whether the quantum gates on the quantum circuit are present in the
native gate set of the quantum hardware.
If this is not the case, the validator will throw a `ValueError`, specifying which gates are present in the circuit's
description, but not in the hardware's native gate set.

## Class Object

```python
PrimitiveGateValidator(native_gate_set: list[str])
```

## Attribute(s)

```python
native_gate_set: A list containing the primitive gate set.
```

The `PrimitiveGateValidator` can be used as such.

```python
from opensquirrel import CircuitBuilder
from opensquirrel.circuit import Circuit
from opensquirrel.passes.validator import NativeGateValidator

primitive_gate_set = ["I", "X90", "mX90", "Y90", "mY90", "Rz", "CZ"]

validator = PrimitiveGateValidator(primtive_gate_set = primitive_gate_set)

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

    ValueError: the following gates are not in the primitive gate set: ['H', 'CNOT']
