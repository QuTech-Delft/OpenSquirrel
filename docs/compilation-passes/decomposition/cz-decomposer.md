The CZ decomposer (`CZDecomposer`) is a two-qubit gate decomposer.
When applied to a circuit, it decomposes every controlled two-qubit gate into a sequence of (at most 2) CZ gates
and single-qubit gates. It decomposes the CR, CRk and CNOT controlled two-qubit gates.

!!! warning "The SWAP gate is not decomposed by the CZ decomposer"

    The SWAP gate is not a _controlled_ two-qubit gate and can therefore not be decomposed using the CZ decomposer.
    To decompose a SWAP gate into either CZ or CNOT gates,
    use the predefined [SWAP to CZ decomposer](predefined-decomposers.md#swap-to-cz-decomposer) (`SWAP2CZDecomposer`)
    or [SWAP to CNOT decomposer](predefined-decomposers.md#swap-to-cnot-decomposer) (`SWAP2CNOTDecomposer`).

!!! note ""

    The CZ gate is more likely to be part of the [primitive gate set](../../tutorial/applying-compilation-passes.md#primitive-gate-set) over the CNOT gate.
    It is therefore recommended to decompose two-qubit controlled gates using the CZ decomposer over the
    [CNOT decomposer](cnot-decomposer.md) (`CNOTDecomposer`).

The algorithm for the CZ decomposer is derived from that of the
[CNOT decomposer](cnot-decomposer.md) (`CNOTDecomposer`), which in turn is based on the the ABC decomposition
(not to be confused with the ABA decomposer). 
The procedure is described in
[Quantum Gates, section 7.5 by G. Crooks (2024)](https://threeplusone.com/pubs/on_gates.pdf).

The single-qubit unitary $U$ of an arbitrary controlled-U gate, can be written as,

$$U = \text{e}^{i\alpha} A \cdot Z \cdot B \cdot Z \cdot C, $$

where $\alpha$ denotes a global phase factor, and the single-qubit unitaries A, B, and C, are chosen such that
$A \cdot B \cdot C = I$. In terms of the latter, the decomposition looks as illustrated below:

![image](../../_static/abc_decomposition_cz.png#only-light)
![image](../../_static/abc_decomposition_cz_dm.png#only-dark)

The ABC decomposition is made using the ABA decomposer,
and in particular, the [XYX decomposer](aba-decomposer.md) (`XYXDecomposer`),
whereby the arbitary U gate is written as,

$$ U = \text{e}^{i\alpha} R_x(\theta_2) \cdot R_y(\theta_1) \cdot R_x(\theta_0), $$

which can be rearranged such that,

$$
\begin{align*}
A& = R_x(\theta_2) \cdot R_y(\theta_1/2), \\ 
B& = R_y(-\theta_1/2) \cdot R_x(-\theta_0/2 - \theta_2/2), \\
C& = R_x(\theta_0/2 - \theta_2/2). \\
\end{align*}
$$

!!! note "Decomposition using a single CZ"

    In certain cases where U can be written as

    $$ U = R_x(\theta_1) \cdot R_y(\theta_0) \cdot R_x(\theta_1) \cdot Z, $$

    only a single CZ is required in the decomposition,
    according to [Lemma 5.5 in Barenco et al. 1995](https://arxiv.org/abs/quant-ph/9503016).
