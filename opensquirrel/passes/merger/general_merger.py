from __future__ import annotations

from abc import ABC, abstractmethod
from math import cos, floor, isclose, log10, sin
from typing import cast

import numpy as np

from opensquirrel import I
from opensquirrel.common import ATOL
from opensquirrel.default_instructions import default_bloch_sphere_rotation_set
from opensquirrel.ir import IR, Barrier, BlochSphereRotation, Float, Instruction, Statement
from opensquirrel.utils import acos, flatten_list


def compose_bloch_sphere_rotations(bsr_a: BlochSphereRotation, bsr_b: BlochSphereRotation) -> BlochSphereRotation:
    """Computes the Bloch sphere rotation resulting from the composition of two Bloch sphere rotations.
    The first rotation is applied and then the second.
    If the final Bloch sphere rotation is anonymous, we will try to match it to a default gate.

    Uses Rodrigues' rotation formula (see https://en.wikipedia.org/wiki/Rodrigues%27_rotation_formula).
    """
    if bsr_a.qubit != bsr_b.qubit:
        msg = "cannot merge two Bloch sphere rotations on different qubits"
        raise ValueError(msg)

    acos_argument = cos(bsr_a.angle / 2) * cos(bsr_b.angle / 2) - sin(bsr_a.angle / 2) * sin(bsr_b.angle / 2) * np.dot(
        bsr_a.axis, bsr_b.axis
    )
    combined_angle = 2 * acos(acos_argument)

    if abs(sin(combined_angle / 2)) < ATOL:
        return I(bsr_a.qubit)

    order_of_magnitude = abs(floor(log10(ATOL)))
    combined_axis = np.round(
        (
            1
            / sin(combined_angle / 2)
            * (
                sin(bsr_a.angle / 2) * cos(bsr_b.angle / 2) * bsr_a.axis.value
                + cos(bsr_a.angle / 2) * sin(bsr_b.angle / 2) * bsr_b.axis.value
                + sin(bsr_a.angle / 2) * sin(bsr_b.angle / 2) * np.cross(bsr_a.axis, bsr_b.axis)
            )
        ),
        order_of_magnitude,
    )

    combined_phase = np.round(bsr_a.phase + bsr_b.phase, order_of_magnitude)

    if bsr_a.is_identity():
        generator = bsr_b.generator
        arguments = bsr_b.arguments
    elif bsr_b.is_identity():
        generator = bsr_a.generator
        arguments = bsr_a.arguments
    elif bsr_a.generator == bsr_b.generator:
        generator = bsr_a.generator
        arguments = (bsr_a.qubit,)
        if bsr_a.arguments is not None and len(bsr_a.arguments) == 2 and isinstance(bsr_a.arguments[1], Float):
            arguments += (Float(combined_angle),)
    else:
        generator = None
        arguments = None

    return try_name_anonymous_bloch(
        BlochSphereRotation(
            qubit=bsr_a.qubit,
            axis=combined_axis,
            angle=combined_angle,
            phase=combined_phase,
            generator=generator,  # type: ignore[arg-type]
            arguments=arguments,
        )
    )


def try_name_anonymous_bloch(bsr: BlochSphereRotation) -> BlochSphereRotation:
    """Try converting a given BlochSphereRotation to a default BlochSphereRotation.
     It does that by checking if the input BlochSphereRotation is close to a default BlochSphereRotation.

    Returns:
         A default BlockSphereRotation if this BlochSphereRotation is close to it,
         or the input BlochSphereRotation otherwise.
    """
    if not bsr.is_anonymous:
        return bsr
    for default_bsr_callable in default_bloch_sphere_rotation_set.values():
        try:
            default_bsr = default_bsr_callable(*bsr.get_qubit_operands())
            if (
                np.allclose(default_bsr.axis, bsr.axis, atol=ATOL)
                and isclose(default_bsr.angle, bsr.angle, rel_tol=ATOL)
                and isclose(default_bsr.phase, bsr.phase, rel_tol=ATOL)
            ):
                return default_bsr
        except TypeError:  # noqa: PERF203
            pass
    return bsr


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
    instruction = cast(Instruction, statement)
    return can_move_statement_before_barrier(instruction, cast(list[Instruction], statement_group))


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
    @abstractmethod
    def merge(self, ir: IR, qubit_register_size: int) -> None:
        raise NotImplementedError
