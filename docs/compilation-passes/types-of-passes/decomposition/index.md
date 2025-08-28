_Gate decomposition_ is a fundamental process in quantum compilation that involves breaking down complex quantum gates
into a sequence of simpler, more elementary gates that can be directly implemented on quantum hardware.
This step is crucial because most quantum processors can only perform a limited set of basic operations,
such as single-qubit rotations and two-qubit entangling gates like the `CNOT` gate.

The importance of gate decomposition lies in its ability to translate high-level quantum algorithms into executable
instructions for quantum hardware. By decomposing complex gates into a series of elementary gates,
the quantum compiler ensures that the algorithm can be run on the available hardware,
regardless of its specific constraints and capabilities.
This process ensures that the quantum algorithm is broken down into a series of gates that match the native gate set of
the hardware.
