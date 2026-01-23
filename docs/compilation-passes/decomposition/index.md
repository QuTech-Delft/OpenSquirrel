Target backends typically are only able to execute a limited set of gates that make up the so-called _native gate set_.
In most cases, the (lower-level) control software of a particular target backend will convert a circuit into these
native gates.

To distinguish between native gates and the set of gates that the control software accepts,
we refer to the latter as the
[_primitive gate set_](../../tutorial/applying-compilation-passes.md#primitive-gate-set).

In general, the native gate set is a subset of the primitive gate set, and the primitive gate set is a subset of the
[standard gate set](https://qutech-delft.github.io/cQASM-spec/latest/standard_gate_set/index.html),
_i.e._, the gate set as supported by the cQASM language.

The input circuit may be written in terms of the the gates as they are defined in the
[standard gate set](https://qutech-delft.github.io/cQASM-spec/latest/standard_gate_set/index.html),
yet the output circuit will need to be in terms of the gates from the primitive gate set.
To ensure the latter, the compiler can be used to _decompose_ the gates into gates that are part of the primitive gate
set.

The following decomposer passes are available in OpenSquirrel:

- [ABA decomposer](aba-decomposer.md)
- [CNOT decomposer](cnot-decomposer.md) (`CNOTDecomposer`)
- [CZ decomposer](cz-decomposer.md) (`CZDecomposer`)
- [McKay decomposer](mckay-decomposer.md) (`McKayDecomposer`)
- [Predefined decomposers](predefined-decomposers.md)
    - [CNOT to CZ decomposer](predefined-decomposers.md#cnot-to-cz-decomposer) (`CNOT2CZDecomposer`)
    - [SWAP to CNOT decomposer](predefined-decomposers.md#swap-to-cnot-decomposer) (`SWAP2CNOTDecomposer`)
    - [SWAP to CZ decomposer](predefined-decomposers.md#swap-to-cnot-decomposer) (`SWAP2CZDecomposer`)

Note that the above decomposers are specific for single- or two-qubit gates;
two-qubit gates are not decomposed by single-qubit gate decomposers, and vice versa.

!!! note "Primitive gate validator"
    
    The [primitive gate validator](../validation/primitive-gate-validator.md) (`PrimitiveGateValidator`) can be used
    to validate that the compiled circuit consists solely of gates that are part of the desired primitive gate set.

!!! warning "Global phase"

    After each decomposition a check is done to ensure that the result constitutes the same unitary operation
    _up to a globale phase difference_. 
    Note that, in general, the global phase is __not__ conserved.
    A difference in global phase can, in certain cases, lead to a semantically different circuit,
    therefore we urge the user to be aware of this risk.

More in depth decomposition tutorials can be found in the [decomposition example Jupyter notebook](https://github.com/QuTech-Delft/OpenSquirrel/blob/develop/example/decompositions.ipynb).
