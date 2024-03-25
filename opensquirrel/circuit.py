from typing import Callable, Dict

import numpy as np

import opensquirrel.parsing.antlr.squirrel_ir_from_string
from opensquirrel import circuit_matrix_calculator, mckay_decomposer, merger, replacer, writer
from opensquirrel.default_gates import default_gate_aliases, default_gate_set
from opensquirrel.export import quantify_scheduler_exporter
from opensquirrel.export_format import ExportFormat
from opensquirrel.parsing.libqasm.libqasm_ir_creator import LibqasmIRCreator
from opensquirrel.replacer import Decomposer
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
        >>> c.decompose(decomposer=mckay_decomposer.McKayDecomposer)
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
        use_libqasm: bool = False,
    ):
        """Create a circuit object from a cQasm3 string. All the gates in the circuit need to be defined in
        the `gates` argument.

        * type-checking is performed, eliminating qubit indices errors and incoherencies
        * checks that used gates are supported and mentioned in `gates` with appropriate signatures
        * does not support map or variables, and other things...
        * for example of `gates` dictionary, please look at TestGates.py


        Args:
            cqasm3_string: a cqasm 3 string
            gate_set: an array of gate semantic functions. See default_gates for examples
            gate_aliases: a dictionary of extra aliases, mapping strings to functions in the gate set
            use_libqasm: if True, use libqasm instead of build-in ANTLR parser.
                Note: those two separate implementations may diverge and libqasm should be taken as reference.

        """
        if use_libqasm:
            libqasm_ir_creator = LibqasmIRCreator(gate_set=gate_set, gate_aliases=gate_aliases)
            return Circuit(libqasm_ir_creator.squirrel_ir_from_string(cqasm3_string))

        return Circuit(
            opensquirrel.parsing.antlr.squirrel_ir_from_string.squirrel_ir_from_string(
                cqasm3_string, gate_set=gate_set, gate_aliases=gate_aliases
            )
        )

    @property
    def number_of_qubits(self) -> int:
        return self.squirrel_ir.number_of_qubits

    @property
    def qubit_register_name(self) -> str:
        return self.squirrel_ir.qubit_register_name

    def merge_single_qubit_gates(self):
        """Merge all consecutive 1-qubit gates in the circuit.
        Gates obtained from merging other gates become anonymous gates.
        """

        merger.merge_single_qubit_gates(self.squirrel_ir)

    def decompose(self, decomposer: Decomposer):
        """Generic decomposition pass. It applies the given decomposer function
        to every gate in the circuit."""
        replacer.decompose(self.squirrel_ir, decomposer)

    def replace(self, gate_generator: Callable[..., Gate], f):
        """Manually replace occurrences of a given gate with a list of gates.
        `f` is a callable that takes the arguments of the gate that is to be replaced
        and returns the decomposition as a list of gates.
        """

        replacer.replace(self.squirrel_ir, gate_generator, f)

    def test_get_circuit_matrix(self) -> np.ndarray:
        """Get the (large) unitary matrix corresponding to the circuit.

        * this matrix has 4**n elements, where n is the number of qubits
        * therefore this function is only here for testing purposes on small number of qubits
        * result is stored as a numpy array of complex numbers
        """

        return circuit_matrix_calculator.get_circuit_matrix(self.squirrel_ir)

    def __repr__(self) -> str:
        """Write the circuit to a cQasm3 string."""

        return writer.squirrel_ir_to_string(self.squirrel_ir)

    def export(self, format: ExportFormat):
        if format == ExportFormat.QUANTIFY_SCHEDULER:
            return quantify_scheduler_exporter.export(self.squirrel_ir)

        raise Exception("Unknown export format")
