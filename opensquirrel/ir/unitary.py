from abc import ABC, abstractmethod
from collections.abc import Sequence

from opensquirrel.common import are_matrices_equivalent_up_to_global_phase
from opensquirrel.ir.expression import Bit, Expression, Qubit
from opensquirrel.ir.statement import Instruction


class Unitary(Instruction, ABC):
    def __init__(self, name: str) -> None:
        Instruction.__init__(self, name)


class Gate(Unitary, ABC):
    def __init__(self, name: str) -> None:
        Unitary.__init__(self, name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Gate):
            return False
        return compare_gates(self, other)

    @property
    @abstractmethod
    def arguments(self) -> tuple[Expression, ...]:
        pass

    @staticmethod
    def _check_repeated_qubit_operands(qubits: Sequence[Qubit]) -> bool:
        return len(qubits) != len(set(qubits))

    @abstractmethod
    def get_qubit_operands(self) -> list[Qubit]:
        pass

    @abstractmethod
    def get_bit_operands(self) -> list[Bit]:
        pass

    @abstractmethod
    def is_identity(self) -> bool:
        pass


def compare_gates(g1: Gate, g2: Gate) -> bool:
    union_mapping = [q.index for q in list(set(g1.get_qubit_operands()) | set(g2.get_qubit_operands()))]

    from opensquirrel.circuit_matrix_calculator import get_circuit_matrix
    from opensquirrel.reindexer import get_reindexed_circuit

    matrix_g1 = get_circuit_matrix(get_reindexed_circuit([g1], union_mapping))
    matrix_g2 = get_circuit_matrix(get_reindexed_circuit([g2], union_mapping))

    return are_matrices_equivalent_up_to_global_phase(matrix_g1, matrix_g2)
