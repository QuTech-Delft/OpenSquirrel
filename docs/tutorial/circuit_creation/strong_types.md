# Strong typing requirements 

As you can see, gates require _strong types_. For instance, you cannot do:

```python
from opensquirrel.circuit import Circuit

try:
    Circuit.from_string(
        """
        version 3.0
        qubit[2] q

        CNOT q[0], 3 // The CNOT expects a qubit as second argument.
        """
    )
except Exception as e:
    print(e)
```
_Output_:

    Parsing error: failed to resolve overload for cnot with argument pack (qubit, int)

The issue is that the `CNOT` expects a qubit as second input argument where an integer has been provided.

