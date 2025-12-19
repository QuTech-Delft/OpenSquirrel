from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, cast

from opensquirrel.ir import IR, Barrier, Instruction, Statement
from opensquirrel.utils import flatten_list


class Merger(ABC):
    def __init__(self, **kwargs: Any) -> None: ...

    @abstractmethod
    def merge(self, ir: IR, qubit_register_size: int) -> None:
        raise NotImplementedError


def can_move_statement_before_barrier(instruction: Instruction, barriers: list[Instruction]) -> bool:
    """Checks whether an instruction can be moved before a group of 'linked' barriers.
    Returns True if none of the qubits used by the instruction are part of any barrier, False otherwise.
    """
    instruction_qubit_operands = instruction.get_qubit_operands()
    barriers_group_qubit_operands = set(flatten_list([barrier.get_qubit_operands() for barrier in barriers]))
    return not any(qubit in barriers_group_qubit_operands for qubit in instruction_qubit_operands)


def can_move_before(statement: Statement, statement_group: list[Statement]) -> bool:
    """Checks whether a statement can be moved before a group of statements, following the logic below:
    - A barrier cannot be moved up.
    - A (non-barrier) statement cannot be moved before another (non-barrier) statement.
    - A (non-barrier) statement may be moved before a group of 'linked' barriers.
    """
    if isinstance(statement, Barrier):
        return False
    first_statement_from_group = statement_group[0]
    if not isinstance(first_statement_from_group, Barrier):
        return False
    instruction = cast("Instruction", statement)
    return can_move_statement_before_barrier(instruction, cast("list[Instruction]", statement_group))


def group_linked_barriers(statements: list[Statement]) -> list[list[Statement]]:
    """Receives a list of statements.
    Returns a list of lists of statements, where each list of statements is
    either a single instruction, or a list of 'linked' barriers (consecutive barriers that cannot be split).
    """
    ret: list[list[Statement]] = []
    index = -1
    adding_linked_barriers_to_group = False
    for statement in statements:
        if not (adding_linked_barriers_to_group and isinstance(statement, Barrier)):
            index += 1
            ret.append([statement])
        else:
            ret[-1].append(statement)
        adding_linked_barriers_to_group = isinstance(statement, Barrier)
    return ret


def rearrange_barriers(ir: IR) -> None:
    """Receives an IR.
    Builds an enumerated list of lists of statements, where each list of statements is
    either a single instruction, or a list of 'linked' barriers (consecutive barriers that cannot be split).
    Then sorts that enumerated list of lists so that instructions can be moved before groups of barriers.
    And updates the input IR with the flattened list of sorted statements.
    """
    statements_groups = group_linked_barriers(ir.statements)
    for i, statement_group in enumerate(statements_groups):
        statement = statement_group[0]
        if not isinstance(statement, Barrier):
            assert len(statement_group) == 1
            previous_statement_groups = reversed(list(enumerate(statements_groups[:i])))
            for j, previous_statement_group in previous_statement_groups:
                if not can_move_before(statement, previous_statement_group):
                    statements_groups.insert(j + 1, [statement])
                    del statements_groups[i + 1]
                    break
    ir.statements = flatten_list(statements_groups)
