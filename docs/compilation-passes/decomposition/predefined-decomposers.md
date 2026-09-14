We refer to a decomposition as being _predefined_ when each instance of a particular gate in the circuit,
_e.g._, the CNOT gate, is replaced with a fixed gate or list of gates.

Four predefined decomposers are available in OpenSquirrel:

- CNOT to CZ decomposer
- SWAP to CNOT decomposer
- SWAP to CZ decomposer
- Three-qubit gate decomposer

!!! note "SWAP decomposition"

    The latter two SWAP decomposers, are currently the only available decomposers in
    OpenSquirrel that can decompose the SWAP gate.
    The general two-qubit decomposers,
    _e.g._, the [CNOT decomposer](cnot-decomposer.md) and [CZ decomposer](cz-decomposer.md) do not decompose
    the SWAP gate.

## CNOT to CZ decomposer

The decomposition of the CNOT gate into a CZ gate (with additional single-qubit gates) is used frequently.
To this end a CNOT to CZ decomposer (`CNOT2CZDecomposer`) has been implemented that decomposes any CNOTs in a circuit 
to a Ry(-π/2), a CZ, and Ry(π/2) gate, in that order; with the single-qubit gates acting on the target qubit.
The decomposition is illustrated in the image below.

![image](../../_static/cnot2cz.png#only-light)
![image](../../_static/cnot2cz_dm.png#only-dark)

Ry gates are used instead of, _e.g._, Hadamard gates, as they are, generally,
more likely to be supported already by target backends.

## SWAP to CNOT decomposer

The SWAP to CNOT decomposer (`SWAP2CNOTDecomposer`) implements the predefined decomposition of the SWAP gate into 3
CNOT gates.
The decomposition is illustrated in the image below.

![image](../../_static/swap2cnot.png#only-light)
![image](../../_static/swap2cnot_dm.png#only-dark)

## SWAP to CZ decomposer

The SWAP to CZ decomposer (`SWAP2CZDecomposer`) implements the predefined decomposition of the SWAP gate into Ry
rotations and 3 CZ gates.
The decomposition is illustrated in the image below.

![image](../../_static/swap2cz.png#only-light)
![image](../../_static/swap2cz_dm.png#only-dark)

## Three-qubit gate decomposer

The three-qubit gate decomposer (`ThreeQubitGateDecomposer`) implements the predefined decomposition of the
Toffoli gate (`CCX`) and the Fredkin gate (`CSWAP`) into CZ gates and single-qubit gates.

The Toffoli gate is decomposed into 6 CZ gates and single-qubit gates, following the circuit described in
[Shende and Markov (2008)](https://arxiv.org/abs/0803.2316),
in which the CNOT gates are further decomposed according to the CNOT to CZ identity described above.
Six is the minimum number of CZ gates required to implement the Toffoli gate,
and this remains the case even when ancilla qubits are available.

The Fredkin gate is decomposed as a Toffoli gate conjugated by two CNOT gates, resulting in 8 CZ gates in total.
Note that, in contrast to the Toffoli gate, it is not known whether this is the minimum number of CZ gates required.

!!! note "Global phase"

    In contrast to the [canonical to CZ decomposer](can2cz-decomposer.md) (`Can2CZDecomposer`),
    the decomposition of the three-qubit gates preserves the global phase of the original gate.

!!! note

    It is advised to run the [single-qubit gates merger](../merging/single-qubit-gates-merger.md)
    (`SingleQubitGatesMerger`) after this decomposition pass.
