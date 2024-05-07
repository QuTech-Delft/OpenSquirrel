from __future__ import annotations

from typing import Callable, Dict

import numpy as np

from opensquirrel.decomposer import general_decomposer
from opensquirrel.decomposer.general_decomposer import Decomposer
from opensquirrel.default_gates import default_gate_aliases, default_gate_set
from opensquirrel.default_measurements import default_measurement_set
from opensquirrel.exporter.export_format import ExportFormat
from opensquirrel.mapper import IdentityMapper, Mapper
from opensquirrel.register_manager import RegisterManager
from opensquirrel.squirrel_ir import Gate, Measure, SquirrelIR


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
        >>> c.decomposer(decomposer=mckay_decomposer.McKayDecomposer)
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

    def __init__(self, register_manager: RegisterManager, squirrel_ir: SquirrelIR):
        """Create a circuit object from a register manager and an IR."""
        self.register_manager = register_manager
        self.squirrel_ir = squirrel_ir

    def __repr__(self) -> str:
        """Write the circuit to a cQASM 3 string."""
        from opensquirrel.exporter import writer

        return writer.circuit_to_string(self)

    def __eq__(self, other):
        return self.register_manager == other.register_manager and self.squirrel_ir == other.squirrel_ir

    @classmethod
    def from_string(
        cls,
        cqasm3_string: str,
        gate_set: [Callable[..., Gate]] = default_gate_set,
        gate_aliases: Dict[str, Callable[..., Gate]] = default_gate_aliases,
        measurement_set: [Callable[..., Measure]] = default_measurement_set,
    ):
        """Create a circuit object from a cQasm3 string. All the gates in the circuit need to be defined in
        the `gates` argument.

        * type-checking is performed, eliminating qubit indices errors and incoherences
        * checks that used gates are supported and mentioned in `gates` with appropriate signatures
        * does not support map or variables, and other things...
        * for example of `gates` dictionary, please look at TestGates.py

        Args:
            cqasm3_string: a cQASM 3 string
            gate_set: an array of gate semantic functions. See default_gates for examples
            gate_aliases: a dictionary of extra gate aliases, mapping strings to functions in the gate set
            measurement_set: an array of measurement semantic functions. See default_measurements for examples
        """
        from opensquirrel.parser.libqasm.parser import Parser

        parser = Parser(
            gate_set=gate_set,
            gate_aliases=gate_aliases,
            measurement_set=measurement_set,
        )
        return parser.circuit_from_string(cqasm3_string)

    @property
    def qubit_register_size(self) -> int:
        return self.register_manager.qubit_register_size

    @property
    def qubit_register_name(self) -> str:
        return self.register_manager.qubit_register_name

    @property
    def bit_register_size(self) -> int:
        return self.register_manager.bit_register_size

    @property
    def bit_register_name(self) -> str:
        return self.register_manager.bit_register_name

    def merge_single_qubit_gates(self):
        """Merge all consecutive 1-qubit gates in the circuit.

        Gates obtained from merging other gates become anonymous gates.
        """
        from opensquirrel.merger import general_merger

        general_merger.merge_single_qubit_gates(self)

    def decompose(self, decomposer: Decomposer):
        """Generic decomposition pass. It applies the given decomposer function to every gate in the circuit."""
        general_decomposer.decompose(self.squirrel_ir, decomposer)

    def map(self, mapper: Mapper) -> None:
        """Generic qubit mapper pass.
        Map the (virtual) qubits of the circuit to the physical qubits of the target hardware.
        """
        from opensquirrel.mapper.qubit_remapper import remap_ir

        remap_ir(self, mapper.get_mapping())

    def replace(self, gate_generator: Callable[..., Gate], f):
        """Manually replace occurrences of a given gate with a list of gates.
        `f` is a callable that takes the arguments of the gate that is to be replaced
        and returns the decomposition as a list of gates.
        """
        general_decomposer.replace(self.squirrel_ir, gate_generator, f)

    def export(self, fmt: ExportFormat = None) -> None:
        if fmt == ExportFormat.QUANTIFY_SCHEDULER:
            from opensquirrel.exporter import quantify_scheduler_exporter

            return quantify_scheduler_exporter.export(self)
        raise ValueError("Unknown exporter format")
