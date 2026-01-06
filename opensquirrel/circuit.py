from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from opensquirrel.ir import AsmDeclaration
from opensquirrel.ir.non_unitary import Measure

if TYPE_CHECKING:
    from opensquirrel.ir.ir import IR
    from opensquirrel.ir.unitary import Gate
    from opensquirrel.passes.decomposer.general_decomposer import Decomposer
    from opensquirrel.passes.exporter.general_exporter import Exporter
    from opensquirrel.passes.mapper.general_mapper import Mapper
    from opensquirrel.passes.merger.general_merger import Merger
    from opensquirrel.passes.router.general_router import Router
    from opensquirrel.passes.validator.general_validator import Validator
    from opensquirrel.register_manager import BitRegister, QubitRegister, RegisterManager


InstructionCount = dict[str, int]
MeasurementToBitMap = defaultdict[str, list[int]]


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
        return writer.circuit_to_string(self, self.is_strict)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Circuit):
            return False
        return self.register_manager == other.register_manager and self.ir == other.ir

    @classmethod
    def from_string(cls, cqasm3_string: str, strict: bool = False) -> Circuit:  # noqa: FBT001, FBT002
        """Create a circuit object from a cQasm3 string. All the gates in the circuit need to be defined in
        the `gates` argument.

        * type-checking is performed, eliminating qubit indices errors and incoherences
        * checks that used gates are supported and mentioned in `gates` with appropriate signatures
        * does not support map or variables, and other things...
        * for example of `gates` dictionary, please look at TestGates.py

        Args:
            cqasm3_string: a cQASM 3 string
        """
        from opensquirrel.reader import LibQasmParser

        cls.is_strict = strict
        return LibQasmParser().circuit_from_string(cqasm3_string)

    @property
    def qubit_register_size(self) -> int:
        return self.register_manager.num_qubits

    @property
    def bit_register_size(self) -> int:
        return self.register_manager.get_bit_register_size()

    @property
    def instruction_count(self) -> InstructionCount:
        """Count the instructions in the circuit by name."""
        counter: Counter[str] = Counter()
        counter.update(
            getattr(statement, "name", "unknown")
            for statement in self.ir.statements
            if not isinstance(statement, AsmDeclaration)
        )
        return dict(counter)

    @property
    def measurement_to_bit_map(self) -> MeasurementToBitMap:
        """Determines and returns the measurement to bit register index mapping."""
        m2b_map: MeasurementToBitMap = defaultdict(list[int])
        for statement in self.ir.statements:
            if isinstance(statement, Measure):
                qubit_index, bit_index = statement.qubit.index, statement.bit.index
                m2b_map[str(qubit_index)].append(bit_index)
        return m2b_map

    def qubit_register_names(self, qubit_register: QubitRegister | None = None) -> list[str] | str:
        if qubit_register:
            return self.register_manager.get_qubit_register_name(qubit_register)
        return [register.name for register in self.register_manager.qubit_registers]

    def bit_register_names(self, bit_register: BitRegister | None = None) -> list[str] | str:
        if bit_register:
            return self.register_manager.get_bit_register_name(bit_register)
        return [register.name for register in self.register_manager.bit_registers]

    def asm_filter(self, backend_name: str) -> None:
        self.ir.statements = [
            statement
            for statement in self.ir.statements
            if not isinstance(statement, AsmDeclaration)
            or (isinstance(statement, AsmDeclaration) and backend_name in str(statement.backend_name))
        ]

    def decompose(self, decomposer: Decomposer) -> None:
        """Generic decomposition pass.
        It applies the given decomposer function to every gate in the circuit.
        """
        from opensquirrel.passes.decomposer import general_decomposer

        general_decomposer.decompose(self.ir, decomposer)

    def export(self, exporter: Exporter) -> Any:
        """Generic export pass.
        Exports the circuit using the specified exporter.

        """
        return exporter.export(self)

    def map(self, mapper: Mapper) -> None:
        """Generic qubit mapper pass.
        Map the (virtual) qubits of the circuit to the physical qubits of the target hardware.
        """
        from opensquirrel.passes.mapper.qubit_remapper import remap_ir

        mapping = mapper.map(self.ir, self.qubit_register_size)
        remap_ir(self, mapping)

    def merge(self, merger: Merger) -> None:
        """Generic merge pass. It applies the given merger to the circuit."""
        merger.merge(self.ir, self.qubit_register_size)

    def route(self, router: Router) -> None:
        """Generic router pass. It applies the given router to the circuit."""
        router.route(self.ir, self.qubit_register_size)

    def replace(self, gate: type[Gate], replacement_gates_function: Callable[..., list[Gate]]) -> None:
        """Manually replace occurrences of a given gate with a list of gates.
        `replacement_gates_function` is a callable that takes the arguments of the gate that is to be replaced and
        returns the decomposition as a list of gates.
        """
        from opensquirrel.passes.decomposer import general_decomposer

        general_decomposer.replace(self.ir, gate, replacement_gates_function)

    def validate(self, validator: Validator) -> None:
        """Generic validator pass. It applies the given validator to the circuit."""
        validator.validate(self.ir)
