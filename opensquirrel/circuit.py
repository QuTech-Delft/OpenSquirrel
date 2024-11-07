from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any

from opensquirrel.default_gates import default_gate_aliases, default_gate_set
from opensquirrel.default_measures import default_measure_set
from opensquirrel.exporter.export_format import ExportFormat

if TYPE_CHECKING:
    from opensquirrel.decomposer import Decomposer
    from opensquirrel.ir import IR, Gate, Measure
    from opensquirrel.mapper import Mapper
    from opensquirrel.register_manager import RegisterManager


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

    def __init__(self, register_manager: RegisterManager, ir: IR) -> None:
        """Create a circuit object from a register manager and an IR."""
        self.register_manager = register_manager
        self.ir = ir

    def __repr__(self) -> str:
        """Write the circuit to a cQASM 3 string."""
        from opensquirrel.writer import writer

        return writer.circuit_to_string(self)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Circuit):
            return False
        return self.register_manager == other.register_manager and self.ir == other.ir

    @classmethod
    def from_string(
        cls,
        cqasm3_string: str,
        gate_set: list[Callable[..., Gate]] = default_gate_set,
        gate_aliases: Mapping[str, Callable[..., Gate]] = default_gate_aliases,
        measure_set: list[Callable[..., Measure]] = default_measure_set,
    ) -> Circuit:
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
            measure_set: an array of measurement semantic functions. See default_measures for examples
        """
        from opensquirrel.parser.libqasm.parser import Parser

        parser = Parser(
            gate_set=gate_set,
            gate_aliases=gate_aliases,
            measure_set=measure_set,
        )
        return parser.circuit_from_string(cqasm3_string)

    @property
    def qubit_register_size(self) -> int:
        return self.register_manager.get_qubit_register_size()

    @property
    def bit_register_size(self) -> int:
        return self.register_manager.get_bit_register_size()

    @property
    def qubit_register_name(self) -> str:
        return self.register_manager.get_qubit_register_name()

    @property
    def bit_register_name(self) -> str:
        return self.register_manager.get_bit_register_name()

    def merge_single_qubit_gates(self) -> None:
        """Merge all consecutive 1-qubit gates in the circuit.
        Gates obtained from merging other gates become anonymous gates.
        """
        from opensquirrel.merger import general_merger

        general_merger.merge_single_qubit_gates(self)

    def optimise(self) -> None:
        """Optimise the circuit by merging the single qubit gates
        and the barriers vertically.
        """
        from opensquirrel.merger import general_merger

        general_merger.optimise_circuit(self)

    def decompose(self, decomposer: Decomposer) -> None:
        """Generic decomposition pass.
        It applies the given decomposer function to every gate in the circuit.
        """
        from opensquirrel.decomposer import general_decomposer

        general_decomposer.decompose(self.ir, decomposer)

    def map(self, mapper: Mapper) -> None:
        """Generic qubit mapper pass.
        Map the (virtual) qubits of the circuit to the physical qubits of the target hardware.
        """
        from opensquirrel.mapper.qubit_remapper import remap_ir

        remap_ir(self, mapper.get_mapping())

    def replace(self, gate_generator: Callable[..., Gate], f: Callable[..., list[Gate]]) -> None:
        """Manually replace occurrences of a given gate with a list of gates.
        `f` is a callable that takes the arguments of the gate that is to be replaced and
        returns the decomposition as a list of gates.
        """
        from opensquirrel.decomposer import general_decomposer

        general_decomposer.replace(self.ir, gate_generator, f)

    def export(self, fmt: ExportFormat | None = None) -> Any:
        if fmt == ExportFormat.QUANTIFY_SCHEDULER:
            from opensquirrel.exporter import quantify_scheduler_exporter

            return quantify_scheduler_exporter.export(self)
        if fmt == ExportFormat.CQASM_V1:
            from opensquirrel.exporter import cqasmv1_exporter

            return cqasmv1_exporter.export(self)
        msg = "unknown exporter format"
        raise ValueError(msg)
