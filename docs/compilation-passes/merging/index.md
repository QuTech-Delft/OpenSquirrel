Merger passes in OpenSquirrel are used to merge gates into single operations.
Their main purpose is to reduce the circuit depth.

Note that the gate that results from merging two gates will in general be an arbitrary operation, _i.e._,
not be a _known_ gate.
In most cases, subsequent [decomposition](../decomposition/index.md) of the gates will be required in order to execute
the circuit on a target backend.
The kind of decomposition pass required will depend on the primitive gate set that the intended backend supports.

OpenSquirrel currently facilitates the following merge pass:

- [Single-qubit gates merger](single-qubit-gates-merger.md) (`SingleQubitGatesMerger`)
