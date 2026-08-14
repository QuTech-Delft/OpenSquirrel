The canonical to CZ decomposer (`Can2CZDecomposer`) is a general two-qubit gate decomposer.
When applied to a circuit, it decomposes every two-qubit gate into a sequence of (at most 3) CZ gates
and single-qubit gates.

Unlike the [CNOT decomposer](cnot-decomposer.md) and [CZ decomposer](cz-decomposer.md),
the canonical to CZ decomposer is not restricted to _controlled_ two-qubit gates.
It can therefore also decompose gates such as the SWAP gate.

!!! warning "Global phase difference"

    Note that the resulting decomposition using the canonical to CZ decomposer (`Can2CZDecomposer`)
    is equal to the original gate, up to a (possible) difference in _global phase_.
    A difference in global phase can, in certain cases, lead to a semantically different circuit,
    therefore we urge the user to be aware of this risk.

The algorithm for the canonical to CZ decomposer is based on the canonical decomposition of an arbitrary two-qubit 
unitary, as described in [Quantum Gates, section 7.3 by G. Crooks (2024)](https://threeplusone.com/pubs/on_gates.pdf).

Any two-qubit unitary $U$ can be written as,

$$
U = (K_1 \otimes K_2) \cdot \text{Can}(t_x,t_y,t_z) \cdot (K_3 \otimes K_4),
$$

where $K_1, K_2, K_3,$ and $K_4$ are single-qubit unitaries, and where the canonical block
$\text{Can}(t_x,t_y,t_z)$ contains the two-qubit interaction, or entangling, part of the gate.

The canonical to CZ decomposer decomposes the canonical block into 
a set of gates consisting of (at most) 3 CNOTs and single-qubit gates.

The CNOT gates are further decomposed into CZ gates according to the predefined CNOT-to-CZ identity:

$$
\mathrm{CNOT}(c,t) = R_y\left(\frac{\pi}{2}\right)_t \cdot \mathrm{CZ}(c,t) \cdot R_y\left(-\frac{\pi}{2}\right)_t,
$$

where $c$ and $t$, respectively represent the control and target qubit:

![image](../../_static/cnot2cz.png#only-light)
![image](../../_static/cnot2cz_dm.png#only-dark)

Finally, the resultant decomposition is placed in between the single-qubit $K$-rotations.

## Decomposition of the canonical block

Depending on the canonical coordinates $(t_x,t_y,t_z)$, the decomposition uses one of three circuit templates,
listed below, to create the decomposition.

### 1. One CNOT gate

For a subset of gates with canonical axis

$$
(t_x,t_y,t_z)=\left(\frac{1}{2},0,0\right),
$$

the decomposition requires only one CNOT gate:

![image](../../_static/can2cz_1.png#only-light)
![image](../../_static/can2cz_1_dm.png#only-dark)

### 2. Two CNOT gates

For gates with

$$
t_z \approx 0,
$$

the decomposition requires two CNOT gates:

![image](../../_static/can2cz_2.png#only-light)
![image](../../_static/can2cz_2_dm.png#only-dark)

### 3. Three CNOT gates

In the general case, the decomposition requires three CNOT gates:

![image](../../_static/can2cz_3.png#only-light)
![image](../../_static/can2cz_3_dm.png#only-dark)

!!! note

    It is advised to run the [single-qubit gates merger](../merging/single-qubit-gates-merger.md)
    (`SingleQubitGatesMerger`) after this decomposition pass.
