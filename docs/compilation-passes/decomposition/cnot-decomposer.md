The CNOT decomposer (`CNOTDecomposer`) is a two-qubit gate decomposer.
When applied to a circuit, it decomposes every (controlled) two-qubit gate into a sequence of (at most 2) CNOT gates
and single-qubit gates.

!!! warning "The SWAP gate is not decomposed by the CNOT decomposer"

    The SWAP gate is not a _controlled_ two-qubit gate and can therefore not be decomposed using the CNOT decomposer.
    To decompose a SWAP gate into either CNOT or CZ gates,
    use the [SWAP to CNOT decomposer](predefined-decomposers.md#swap-to-cnot-decomposer) (`SWAP2CNOTDecomposer`)
    or the [SWAP to CZ decomposer](predefined-decomposers.md#swap-to-cz-decomposer) (`SWAP2CZDecomposer`).

The algorithm for the CNOT decomposer is based on the ABC decomposition (not to be confused with the ABA decomposer).

[On gates: Section 7.4: ABC decomposition](https://threeplusone.com/pubs/on_gates.pdf)
