from typing import Callable, Dict

import numpy as np

from opensquirrel import circuit_matrix_calculator, mckay_decomposer, replacer, writer
from opensquirrel.default_gates import default_gate_aliases, default_gate_set
from opensquirrel.parsing.antlr.squirrel_ir_from_string import squirrel_ir_from_string
from opensquirrel.squirrel_ir import Gate, SquirrelIR


class Circuit:
    """The Circuit class is the only interface to access OpenSquirrel's features.

    Examples:
        >>> c = Circuit.from_string("version 3.0; qubit[3] q; h q[0]")
        >>> c
        version 3.0
        <BLANKLINE>
        qubit[3] q
        <BLANKLINE>
        h q[0]
        <BLANKLINE>
        >>> c.decompose_mckay()
        >>> c
        version 3.0
        <BLANKLINE>
        qubit[3] q
        <BLANKLINE>
        x90 q[0]
        rz q[0], 1.5707963
        x90 q[0]
        <BLANKLINE>
    """

    def __init__(self, squirrel_ir: SquirrelIR):
        """Create a circuit object from a SquirrelIR object."""

        self.squirrel_ir = squirrel_ir

    @classmethod
    def from_string(
        cls,
        cqasm3_string: str,
        gate_set: [Callable[..., Gate]] = default_gate_set,
        gate_aliases: Dict[str, Callable[..., Gate]] = default_gate_aliases,
    ):
        """Create a circuit object from a cQasm3 string. All the gates in the circuit need to be defined in
        the `gates` argument.

        * type-checking is performed, eliminating qubit indices errors and incoherencies
        * checks that used gates are supported and mentioned in `gates` with appropriate signatures
        * does not support map or variables, and other things...
        * for example of `gates` dictionary, please look at TestGates.py
        """

        return Circuit(squirrel_ir_from_string(cqasm3_string, gate_set=gate_set, gate_aliases=gate_aliases))

    @property
    def number_of_qubits(self) -> int:
        return self.squirrel_ir.number_of_qubits

    @property
    def qubit_register_name(self) -> str:
        return self.squirrel_ir.qubit_register_name

    def decompose_mckay(self):
        """Perform gate fusion on all one-qubit gates and decompose them in the McKay style.

        * all one-qubit gates on same qubit are merged together, without attempting to commute any gate
        * two-or-more-qubit gates are left as-is
        * merged one-qubit gates are decomposed according to McKay decomposition, that is:
                gate   ---->    Rz.Rx(pi/2).Rz.Rx(pi/2).Rz
        * _global phase is deemed irrelevant_, therefore a simulator backend might produce different output
            for the input and output circuit - those outputs should be equivalent modulo global phase.
        """

        self.squirrel_ir = mckay_decomposer.decompose_mckay(self.squirrel_ir)  # FIXME: inplace

    def replace(self, gate_name: str, f):
        """Manually replace occurrences of a given gate with a list of gates.

        * this can be called decomposition - but it's the least fancy version of it
        * function parameter gives the decomposition based on parameters of original gate
        """

        replacer.replace(self.squirrel_ir, gate_name, f)

    def test_get_circuit_matrix(self) -> np.ndarray:
        """Get the (large) unitary matrix corresponding to the circuit.

        * this matrix has 4**n elements, where n is the number of qubits
        * therefore this function is only here for testing purposes on small number of qubits
        * result is stored as a numpy array of complex numbers
        """

        return circuit_matrix_calculator.get_circuit_matrix(self.squirrel_ir)

    def __repr__(self) -> str:
        """Write the circuit to a cQasm3 string.

        * comments are removed
        """

        return writer.squirrel_ir_to_string(self.squirrel_ir)
