from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from math import acos, cos, floor, log10, sin
from typing import Callable, cast

import numpy as np

from opensquirrel import I
from opensquirrel.common import ATOL
from opensquirrel.default_instructions import default_bloch_sphere_rotation_set
from opensquirrel.ir import IR, Barrier, BlochSphereRotation, Float, Instruction, Statement
from opensquirrel.utils import flatten_list


def compose_bloch_sphere_rotations(a: BlochSphereRotation, b: BlochSphereRotation) -> BlochSphereRotation:
    """Computes the Bloch sphere rotation resulting from the composition of two Bloch sphere rotations.
    The first rotation is applied and then the second.
    The resulting gate is anonymous except if:
    - `a` is the identity and `b` is not anonymous, or vice versa, or
    - `a` and `b` are the same named gate (have the same generator).

    Uses Rodrigues' rotation formula, see for instance https://en.wikipedia.org/wiki/Rodrigues%27_rotation_formula.
    """
    if a.qubit != b.qubit:
        msg = "cannot merge two BlochSphereRotation's on different qubits"
        raise ValueError(msg)

    acos_argument = cos(a.angle / 2) * cos(b.angle / 2) - sin(a.angle / 2) * sin(b.angle / 2) * np.dot(a.axis, b.axis)
    # This fixes float approximations like 1.0000000000002 which acos doesn't like.
    acos_argument = max(min(acos_argument, 1.0), -1.0)

    combined_angle = 2 * acos(acos_argument)

    if abs(sin(combined_angle / 2)) < ATOL:
        return I(a.qubit)

    order_of_magnitude = abs(floor(log10(ATOL)))
    combined_axis = np.round(
        (
            1
            / sin(combined_angle / 2)
            * (
                sin(a.angle / 2) * cos(b.angle / 2) * a.axis.value
                + cos(a.angle / 2) * sin(b.angle / 2) * b.axis.value
                + sin(a.angle / 2) * sin(b.angle / 2) * np.cross(a.axis, b.axis)
            )
        ),
        order_of_magnitude,
    )

    combined_phase = np.round(a.phase + b.phase, order_of_magnitude)

    if a.is_identity():
        generator = b.generator
        arguments = b.arguments
    elif b.is_identity():
        generator = a.generator
        arguments = a.arguments
    elif a.generator == b.generator:
        generator = a.generator
        arguments = (a.qubit, Float(combined_angle))
    else:
        generator = None
        arguments = (a.qubit,)

    return BlochSphereRotation(
        qubit=a.qubit,
        axis=combined_axis,
        angle=combined_angle,
        phase=combined_phase,
        generator=generator,  # type: ignore[arg-type]
        arguments=arguments,
    )


def can_invoke_bsr_callable(bsr_callable: Callable[..., BlochSphereRotation], bsr: BlochSphereRotation) -> bool:
    """Given a callable that returns a BSR and a BSR.
    Check that the BSR returned by the callable can be invoked with the arguments of the BSR instance.

    Args:
        bsr_callable: A callable returning a BlochSphereRotation object.
        bsr: A BlochSphereRotation instance.

    Returns:
        True if the BSR returned by the callable can be invoked with the arguments of the BSR instance, False otherwise.
    """
    bsr_callable_signature = inspect.signature(bsr_callable)
    bsr_callable_param_types = [
        param.annotation
        for param in bsr_callable_signature.parameters.values()
        if param.annotation is not inspect.Parameter.empty
    ]

    bsr_arg_types = [type(arg) for arg in bsr.arguments] if bsr.arguments is not None else []

    # Check we have the same number of arguments and parameters, and arguments types can be used as parameters
    return len(bsr_arg_types) == len(bsr_callable_param_types) and all(
        issubclass(bsr_arg_type, bsr_callable_param_type)
        if isinstance(bsr_callable_param_type, type)
        else bsr_arg_type == bsr_callable_param_type
        for bsr_arg_type, bsr_callable_param_type in zip(bsr_arg_types, bsr_callable_param_types)
    )


def try_name_anonymous_bloch(bsr: BlochSphereRotation) -> BlochSphereRotation:
    """Try converting a given BlochSphereRotation to a default BlochSphereRotation.
     It does that by checking if the input BlochSphereRotation is close to a default BlochSphereRotation.

    Notice we don't try to match Rx, Ry, and Rz rotations, as those gates use an extra angle parameter.

    Returns:
         A default BlockSphereRotation if this BlochSphereRotation is close to it,
         or the input BlochSphereRotation otherwise.
    """
    for default_bsr_callable in default_bloch_sphere_rotation_set.values():
        if can_invoke_bsr_callable(default_bsr_callable, bsr):
            default_bsr = default_bsr_callable(*bsr.get_qubit_operands())
            if (
                np.allclose(default_bsr.axis, bsr.axis, atol=ATOL)
                and np.allclose(default_bsr.angle, bsr.angle, atol=ATOL)
                and np.allclose(default_bsr.phase, bsr.phase, atol=ATOL)
            ):
                return default_bsr
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
