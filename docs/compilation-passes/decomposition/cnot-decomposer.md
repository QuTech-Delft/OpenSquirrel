The CNOT decomposer (`CNOTDecomposer`) is a two-qubit gate decomposer.
When applied to a circuit, it decomposes every controlled two-qubit gate into a sequence of (at most 2) CNOT gates
and single-qubit gates. It decomposes the CR, CRk and CZ controlled two-qubit gates.

!!! warning "The SWAP gate is not decomposed by the CNOT decomposer"

    The SWAP gate is not a _controlled_ two-qubit gate and can therefore not be decomposed using the CNOT decomposer.
    To decompose a SWAP gate into either CNOT or CZ gates,
    use the predefined 
    [SWAP to CNOT decomposer](predefined-decomposers.md#swap-to-cnot-decomposer) (`SWAP2CNOTDecomposer`)
    or [SWAP to CZ decomposer](predefined-decomposers.md#swap-to-cz-decomposer) (`SWAP2CZDecomposer`).

!!! note ""

    The CNOT gate is, in general, not part of the
    [primitive gate set](../../tutorial/applying-compilation-passes.md#primitive-gate-set) of a target backend.
    The CZ gate is more likely to be part of the primitive gate set.
    After using the CNOT decomposer one could use the
    [CNOT to CZ decomposer](predefined-decomposers.md#cnot-to-cz-decomposer) (`CNOT2CZDecomposer`)
    or, instead of using the CNOT decomposer all together, simply decompose the two-qubit controlled gates
    using the [CZ decomposer](cz-decomposer.md). 


The algorithm for the CNOT decomposer is based on the ABC decomposition (not to be confused with the ABA decomposer).
The procedure is described in
[Quantum Gates, section 7.5 by G. Crooks (2024)](https://threeplusone.com/pubs/on_gates.pdf).

The single-qubit unitary $U$ of an arbitrary controlled-U gate, can be written as,

$$U = \text{e}^{i\alpha} A \cdot X \cdot B \cdot X \cdot C, $$

where $\alpha$ denotes a global phase factor, and the single-qubit unitaries $A$, $B$, and $C$, are chosen such that
$A \cdot B \cdot C = I$.
In terms of the latter, the decomposition looks as illustrated below:

![image](../../_static/abc_decomposition.png#only-light)
![image](../../_static/abc_decomposition_dm.png#only-dark)

The ABC decomposition is made using the ABA decomposer,
and in particular, the [ZYZ decomposer](aba-decomposer.md) (`ZYZDecomposer`),
whereby the arbitary unitary $U$ is written as,

$$ U = \text{e}^{i\alpha} R_z(\theta_2) \cdot R_y(\theta_1) \cdot R_z(\theta_0), $$

which can be rearranged such that,

$$
\begin{align*}
A& = R_z(\theta_2) \cdot R_y(\theta_1/2), \\ 
B& = R_y(-\theta_1/2) \cdot R_z(-\theta_0/2 - \theta_2/2), \\
C& = R_z(\theta_0/2 - \theta_2/2). \\
\end{align*}
$$

!!! note "Decomposition using a single CNOT"

    In certain cases where the unitary $U$ can be written as

    $$ U = R_z(\theta_1) \cdot R_z(\theta_0) \cdot R_z(\theta_1) \cdot X, $$

    only a single CNOT gate is required in the decomposition,
    according to [Lemma 5.5 in Barenco et al. 1995](https://arxiv.org/abs/quant-ph/9503016).
