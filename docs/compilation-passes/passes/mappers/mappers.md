# Mapping Passes

_Qubit mapping_, also known as _initial mapping_, is a critical step in the quantum compilation process. It involves assigning logical qubits, which are used in the quantum algorithm, to physical qubits available on the quantum hardware. This mapping is essential because the physical qubits on a quantum processor have specific connectivity constraints, meaning not all qubits can directly interact with each other. The initial mapping must respect these constraints to ensure that the required two-qubit gates can be executed without violating the hardware's connectivity limitations.

A poor initial mapping can lead to a high number of SWAP operations, which are used to move qubits into positions where they can interact. SWAP operations increase the circuit depth and introduce additional errors. An optimal initial mapping minimizes the need for these operations, thereby reducing the overall error rate and improving the fidelity of the quantum computation. Efficient qubit mapping can significantly enhance the performance of the quantum circuit. By strategically placing qubits, the compiler can reduce the number of additional operations required, leading to faster and more reliable quantum computations.

# Available Mapper Passes 

_OpenSquirrel_ faciliates the following mapper passes.

## Identity Mapper

The Identity Mapper simply maps each virtual qubit on the circuit to its corresponding physical qubit on the device, index-wise. 

## Hardcoded Mapper

With this mapper, the initial mapping is simply hardcoded. 

## Random Mapper

This mapper pass generates a random initial mapping from virtual qubits from physical qubits. 