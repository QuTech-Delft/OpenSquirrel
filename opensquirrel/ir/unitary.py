from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from opensquirrel.common import are_matrices_equivalent_up_to_global_phase
from opensquirrel.ir.statement import Instruction

if TYPE_CHECKING:
    from opensquirrel.ir import Bit, IRVisitor, Qubit
    from opensquirrel.ir.expression import Expression


class Unitary(Instruction, ABC):
    def __init__(self, name: str) -> None:
        Instruction.__init__(self, name)


class Gate(Unitary, ABC):
    def __init__(self, name: str) -> None:
        Unitary.__init__(self, name)

    @staticmethod
    def _check_repeated_qubit_operands(qubits: Sequence[Qubit]) -> bool:
        return len(qubits) != len(set(qubits))

    @abstractmethod
    def is_identity(self) -> bool: ...

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return ()

    @property
    def bit_operands(self) -> tuple[Bit, ...]:
        return ()

    def accept(self, visitor: IRVisitor) -> Any:
        """Accepts visitor and processes this IR node."""
        return visitor.visit_gate(self)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Gate):
            return False
        return compare_gates(self, other)


def compare_gates(gate_1: Gate, gate_2: Gate) -> bool:
    """Checks if two gates are equivalent up to a global phase.

    Args:
        gate_1 (Gate): The first gate to compare.
        gate_2 (Gate): The second gate to compare.

    Returns:
        True if the two gates are equivalent up to a global phase, False otherwise.

    """
    union_mapping = list(set(gate_1.qubit_indices) | set(gate_2.qubit_indices))

    from opensquirrel.circuit_matrix_calculator import get_circuit_matrix
    from opensquirrel.reindexer import get_reindexed_circuit

    matrix_gate_1 = get_circuit_matrix(get_reindexed_circuit([gate_1], union_mapping))
    matrix_gate_2 = get_circuit_matrix(get_reindexed_circuit([gate_2], union_mapping))

    return are_matrices_equivalent_up_to_global_phase(matrix_gate_1, matrix_gate_2)
