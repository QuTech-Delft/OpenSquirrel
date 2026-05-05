from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable
from itertools import combinations
from typing import TYPE_CHECKING, Any

from opensquirrel.ir import Instruction
from opensquirrel.ir.non_unitary import Measure
from opensquirrel.ir.statement import AsmDeclaration
from opensquirrel.passes.mapper import IdentityMapper

if TYPE_CHECKING:
    from opensquirrel.ir.ir import IR
    from opensquirrel.ir.unitary import Gate
    from opensquirrel.passes.analyzer.general_analyzer import Analyzer
    from opensquirrel.passes.decomposer.general_decomposer import Decomposer
    from opensquirrel.passes.exporter.general_exporter import Exporter
    from opensquirrel.passes.mapper.general_mapper import Mapper
    from opensquirrel.passes.merger.general_merger import Merger
    from opensquirrel.passes.router.general_router import Router
    from opensquirrel.passes.validator.general_validator import Validator
    from opensquirrel.register_manager import RegisterManager


InstructionCount = dict[str, int]
MeasurementToBitMap = defaultdict[str, list[int]]
InteractionGraph = dict[tuple[int, int], int]


class Circuit:
    """The Circuit class is the only interface to access OpenSquirrel's features.

    Example:
        ```python
        >>> circuit = Circuit.from_string("version 3.0; qubit[3] q; h q[0]")
        >>> circuit
        ```
        ```
        version 3.0

        qubit[3] q

        h q[0]
        ```
        ```python
        >>> circuit.decompose(decomposer=McKayDecomposer())
        >>> circuit
        ```
        ```
        version 3.0

        qubit[3] q

        x90 q[0]
        rz q[0], 1.5707963
        x90 q[0]

        ```

    """

    def __init__(self, register_manager: RegisterManager, ir: IR) -> None:
        """Create a circuit object from a register manager and an IR."""
        self.register_manager = register_manager
        self.ir = ir
        self.mapping = IdentityMapper().map(self, self.qubit_register_size)

    @classmethod
    def from_string(cls, cqasm_string: str) -> Circuit:
        """Create a circuit from a [cQASM](https://qutech-delft.github.io/cQASM-spec/) string.

        Args:
            cqasm_string (str): A cQASM string.

        Returns:
            Circuit: The circuit generated from the cQASM string.

        """
        from opensquirrel.reader import LibQasmParser

        return LibQasmParser().circuit_from_string(cqasm_string)

    @property
    def qubit_register_size(self) -> int:
        return self.register_manager.qubit_register_size

    @property
    def bit_register_size(self) -> int:
        return self.register_manager.bit_register_size

    @property
    def qubit_register_name(self) -> str:
        return self.register_manager.qubit_register_name

    @property
    def bit_register_name(self) -> str:
        return self.register_manager.bit_register_name

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

    @property
    def interaction_graph(self) -> InteractionGraph:
        """Interaction graph of the circuit."""
        graph = {}
        for statement in self.ir.statements:
            if not isinstance(statement, Instruction):
                continue
            qubit_indices = statement.qubit_indices
            if len(qubit_indices) >= 2:
                for q_i, q_j in combinations(qubit_indices, 2):
                    edge = (min(q_i, q_j), max(q_i, q_j))
                    graph[edge] = graph.get(edge, 0) + 1
        return graph

    def asm_filter(self, backend_name: str) -> None:
        """Filter the assembly declarations in the circuit for a specific backend.

        Note:
            This will remove all assembly declarations that do not match the specified backend name.

        Args:
            backend_name (str): The backend name to filter for.

        """
        self.ir.statements = [
            statement
            for statement in self.ir.statements
            if not isinstance(statement, AsmDeclaration)
            or (isinstance(statement, AsmDeclaration) and backend_name in str(statement.backend_name))
        ]

    def analyze(self, analyzer: Analyzer) -> dict[str, Any]:
        """Analyzes the circuit using the specified analyzer.

        Args:
             analyzer (Analyzer): The analyzer to apply.

        Returns:
            dict[str, Any]: The metrics computed by the analyzer.

        """
        return analyzer.analyze(self)

    def decompose(self, decomposer: Decomposer) -> None:
        """Decomposes the circuit using to the specified decomposer.

        Args:
            decomposer (Decomposer): The decomposer to apply.

        """
        from opensquirrel.passes.decomposer.general_decomposer import decompose

        decompose(self.ir, decomposer)

    def export(self, exporter: Exporter) -> Any:
        """Exports the circuit using the specified exporter.

        Args:
            exporter (Exporter): The exporter to apply.

        """
        return exporter.export(self)

    def map(self, mapper: Mapper) -> None:
        """Maps the (virtual) qubits of the circuit to the physical qubits of the target hardware
        using the specified mapper.

        Args:
            mapper (Mapper): The mapper to apply.

        """
        from opensquirrel.passes.mapper.qubit_remapper import remap_ir

        self.mapping = mapper.map(self, self.qubit_register_size)

        remap_ir(self, self.mapping)

    def merge(self, merger: Merger) -> None:
        """Merges the circuit using the specified merger.

        Args:
            merger (Merger): The merger to apply.

        """
        merger.merge(self.ir, self.qubit_register_size)

    def route(self, router: Router) -> None:
        """Routes the circuit using the specified router.

        Args:
            router (Router): The router to apply.

        """
        router.route(self.ir, self.qubit_register_size)

    def replace(self, gate: type[Gate], replacement_gates_function: Callable[..., list[Gate]]) -> None:
        """Manually replace occurrences of a given gate with a list of gates.

        Args:
            gate (type[Gate]): The gate type to be replaced.
            replacement_gates_function (Callable[..., list[Gate]]): function that describes the replacement gates.

        """
        from opensquirrel.passes.decomposer.gate_replacer import replace

        replace(self.ir, gate, replacement_gates_function)

    def validate(self, validator: Validator) -> None:
        """Validates the circuit using the specified validator.

        Args:
            validator (Validator): The validator to apply.

        """
        validator.validate(self.ir)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Circuit):
            return False
        return self.register_manager == other.register_manager and self.ir == other.ir

    def __repr__(self) -> str:
        """Write the circuit to a cQASM 3 string."""
        from opensquirrel.writer import writer

        return writer.circuit_to_string(self)
