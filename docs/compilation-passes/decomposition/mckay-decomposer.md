The McKay decomposer (`McKayDecomposer`) is a single-qubit gate decomposer.

It decomposes any single-qubit unitary $U$ into a sequence of (at most 5) single-qubit gates,
consisting of Rz and Rx rotations:

$$U = R_z(\theta) \cdot R_x(\pi/2) \cdot R_z(\phi) \cdot R_x(\pi/2) \cdot R_z(\lambda). $$

The algorithm used by the McKay decomposer is described in
[McKay et al. (2017)](https://arxiv.org/abs/1612.00858).

!!! warning "Global phase difference"

    Note that the resulting decomposition using the McKay decomposer (`McKayDecomposer`)
    is equal to the original gate, up to a (possible) difference in _global phase_.
    A difference in global phase can, in certain cases, lead to a semantically different circuit,
    therefore we urge the user to be aware of this risk.

Example decompositions of notable single-qubit gates are:

|Unitary|Decomposition                            |
|-------|-----------------------------------------|
|I      |$I$                                      |  
|H      |$Rz(\pi/2) \cdot X^{1/2} \cdot Rz(\pi/2)$| 
|X      |$X^{1/2} \cdot X^{1/2}$                  | 
|Y      |$X^{1/2} \cdot X^{1/2} \cdot Rz(\pi)$    | 
|Z      |$Rz(\pi)$                                |
|S      |$Rz(\pi/2)$                              |
|T      |$Rz(\pi/4)$                              |
