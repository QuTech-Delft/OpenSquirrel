from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from opensquirrel.passes.exporter import ExportFormat

if TYPE_CHECKING:
    from opensquirrel.ir import IR, Gate
    from opensquirrel.passes.decomposer import Decomposer
    from opensquirrel.passes.mapper import Mapper
    from opensquirrel.passes.merger.general_merger import Merger
    from opensquirrel.passes.router.general_router import Router
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
        from opensquirrel import writer

        return writer.circuit_to_string(self)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Circuit):
            return False
        return self.register_manager == other.register_manager and self.ir == other.ir

    @classmethod
    def from_string(cls, cqasm3_string: str) -> Circuit:
        """Create a circuit object from a cQasm3 string. All the gates in the circuit need to be defined in
        the `gates` argument.

        * type-checking is performed, eliminating qubit indices errors and incoherences
        * checks that used gates are supported and mentioned in `gates` with appropriate signatures
        * does not support map or variables, and other things...
        * for example of `gates` dictionary, please look at TestGates.py

        Args:
            cqasm3_string: a cQASM 3 string
        """
        from opensquirrel.parser.libqasm.parser import Parser

        return Parser().circuit_from_string(cqasm3_string)

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

    def route(self, router: Router) -> None:
        """Generic router pass. It applies the given Router to the circuit."""
        router.route(self.ir)

    def merge(self, merger: Merger) -> None:
        """Generic merge pass. It applies the given merger to the circuit."""
        merger.merge(self.ir, self.qubit_register_size)

    def decompose(self, decomposer: Decomposer) -> None:
        """Generic decomposition pass.
        It applies the given decomposer function to every gate in the circuit.
        """
        from opensquirrel.passes.decomposer import general_decomposer

        general_decomposer.decompose(self.ir, decomposer)

    def map(self, mapper: Mapper) -> None:
        """Generic qubit mapper pass.
        Map the (virtual) qubits of the circuit to the physical qubits of the target hardware.
        """
        from opensquirrel.passes.mapper.qubit_remapper import remap_ir

        remap_ir(self, mapper.get_mapping())

    def replace(self, gate_generator: Callable[..., Gate], f: Callable[..., list[Gate]]) -> None:
        """Manually replace occurrences of a given gate with a list of gates.
        `f` is a callable that takes the arguments of the gate that is to be replaced and
        returns the decomposition as a list of gates.
        """
        from opensquirrel.passes.decomposer import general_decomposer

        general_decomposer.replace(self.ir, gate_generator, f)

    def export(self, fmt: ExportFormat | None = None) -> Any:
        if fmt == ExportFormat.QUANTIFY_SCHEDULER:
            from opensquirrel.passes.exporter import quantify_scheduler_exporter

            return quantify_scheduler_exporter.export(self)
        if fmt == ExportFormat.CQASM_V1:
            from opensquirrel.passes.exporter import cqasmv1_exporter

            return cqasmv1_exporter.export(self)
        msg = "unknown exporter format"
        raise ValueError(msg)
