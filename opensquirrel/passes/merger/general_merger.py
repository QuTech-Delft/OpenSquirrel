from __future__ import annotations

from abc import ABC, abstractmethod
from math import cos, floor, log10, sin
from typing import Any, cast

import numpy as np

from opensquirrel import I
from opensquirrel.common import ATOL
from opensquirrel.ir import IR, Barrier, Instruction, Statement
from opensquirrel.ir.semantics import BlochSphereRotation
from opensquirrel.ir.single_qubit_gate import SingleQubitGate, try_match_replace_with_default_gate
from opensquirrel.utils import acos, flatten_list


def compose_bloch_sphere_rotations(gate_a: SingleQubitGate, gate_b: SingleQubitGate) -> SingleQubitGate:
    """Computes the Bloch sphere rotation resulting from the composition of two Bloch sphere rotations.
    The first rotation (A) is applied and then the second (B):

    As separate gates:
        A q
        B q

    As linear operations:
        (B * A) q

    If the final Bloch sphere rotation is anonymous, we try to match it to a default gate.

    Uses Rodrigues' rotation formula (see https://en.wikipedia.org/wiki/Rodrigues%27_rotation_formula).
    """

    if gate_a.qubit != gate_b.qubit:
        msg = "cannot merge two Bloch sphere rotations on different qubits"
        raise ValueError(msg)

    acos_argument = cos(gate_a.bsr.angle / 2) * cos(gate_b.bsr.angle / 2) - sin(gate_a.bsr.angle / 2) * sin(
        gate_b.bsr.angle / 2
    ) * np.dot(gate_a.bsr.axis, gate_b.bsr.axis)
    combined_angle = 2 * acos(acos_argument)

    if abs(sin(combined_angle / 2)) < ATOL:
        return I(gate_a.qubit)

    order_of_magnitude = abs(floor(log10(ATOL)))
    combined_axis = np.round(
        (
            1
            / sin(combined_angle / 2)
            * (
                sin(gate_a.bsr.angle / 2) * cos(gate_b.bsr.angle / 2) * gate_a.bsr.axis.value
                + cos(gate_a.bsr.angle / 2) * sin(gate_b.bsr.angle / 2) * gate_b.bsr.axis.value
                + sin(gate_a.bsr.angle / 2) * sin(gate_b.bsr.angle / 2) * np.cross(gate_b.bsr.axis, gate_a.bsr.axis)
            )
        ),
        order_of_magnitude,
    )

    combined_phase = np.round(gate_a.bsr.phase + gate_b.bsr.phase, order_of_magnitude)
    bsr = BlochSphereRotation(
        axis=combined_axis,
        angle=combined_angle,
        phase=combined_phase,
    )
    gate = SingleQubitGate(gate_a.qubit, bsr)
    return try_match_replace_with_default_gate(gate)


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


class Merger(ABC):
    def __init__(self, **kwargs: Any) -> None: ...

    @abstractmethod
    def merge(self, ir: IR, qubit_register_size: int) -> None:
        raise NotImplementedError
