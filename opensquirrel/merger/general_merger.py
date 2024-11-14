from __future__ import annotations

from math import acos, cos, floor, log10, sin
from typing import TYPE_CHECKING

import numpy as np

from opensquirrel.common import ATOL
from opensquirrel.default_gates import I, default_bloch_sphere_rotations_without_params
from opensquirrel.ir import IR, Barrier, BlochSphereRotation, Comment, Qubit, Statement
from opensquirrel.utils.list import flatten_list

if TYPE_CHECKING:
    from opensquirrel.circuit import Circuit


def compose_bloch_sphere_rotations(a: BlochSphereRotation, b: BlochSphereRotation) -> BlochSphereRotation:
    """Computes the Bloch sphere rotation resulting from the composition of two Bloch sphere rotations.
    The first rotation is applied and then the second.
    The resulting gate is anonymous except if `a` is the identity and `b` is not anonymous, or vice versa.

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
        return BlochSphereRotation.identity(a.qubit)

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

    generator = b.generator if a.is_identity() else a.generator if b.is_identity() else None
    arguments = b.arguments if a.is_identity() else a.arguments if b.is_identity() else None

    return BlochSphereRotation(
        qubit=a.qubit,
        axis=combined_axis,
        angle=combined_angle,
        phase=combined_phase,
        generator=generator,  # type: ignore[arg-type]
        arguments=arguments,
    )


def try_name_anonymous_bloch(bsr: BlochSphereRotation) -> BlochSphereRotation:
    """Try converting a given BlochSphereRotation to a default BlochSphereRotation.
     It does that by checking if the input BlochSphereRotation is close to a default BlochSphereRotation.

    Notice we don't try to match Rx, Ry, and Rz rotations, as those gates use an extra angle parameter.

    Returns:
         A default BlockSphereRotation if this BlochSphereRotation is close to it,
         or the input BlochSphereRotation otherwise.
    """
    for gate_function in default_bloch_sphere_rotations_without_params:
        gate = gate_function(*bsr.get_qubit_operands())
        if (
            np.allclose(gate.axis, bsr.axis)
            and np.allclose(gate.angle, bsr.angle)
            and np.allclose(gate.phase, bsr.phase)
        ):
            return gate
    return bsr


def can_move_instruction_before_barrier(instruction: Statement, barriers: list[Statement]) -> bool:
    """Checks whether an instruction can be moved before a group of 'linked' barriers.
    Returns True if none of the qubits used by the instruction are part of any barrier, False otherwise.
    """
    instruction_qubit_operands = instruction.get_qubit_operands()
    barriers_group_qubit_operands = set(flatten_list([barrier.get_qubit_operands() for barrier in barriers]))
    return not any(qubit in barriers_group_qubit_operands for qubit in instruction_qubit_operands)


def can_move_before(statement: Statement, statement_group: list[Statement]) -> bool:
    """Checks whether a statement can be moved before a group of statements, following the logic below:
    - An instruction cannot be moved before other instruction.
    - An instruction may be moved before a group of 'linked' barriers.
    """
    first_statement_from_group = statement_group[0]
    if not isinstance(statement, Barrier) and not isinstance(first_statement_from_group, Barrier):
        return False
    if not isinstance(statement, Barrier) and isinstance(first_statement_from_group, Barrier):
        return can_move_instruction_before_barrier(statement, statement_group)
    if isinstance(statement, Barrier) and not isinstance(first_statement_from_group, Barrier):
        return can_move_instruction_before_barrier(statement, statement_group)
    return False


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


def merge_single_qubit_gates(circuit: Circuit) -> None:  # noqa: C901
    """Merge all consecutive 1-qubit gates in the circuit.

    Gates obtained from merging other gates become anonymous gates.

    Args:
        circuit: Circuit to perform the merge on.
    """
    accumulators_per_qubit: dict[Qubit, BlochSphereRotation] = {
        Qubit(qubit_index): I(qubit_index) for qubit_index in range(circuit.qubit_register_size)
    }

    statement_index = 0
    while statement_index < len(circuit.ir.statements):
        statement = circuit.ir.statements[statement_index]

        # Skip, since statement is a comment
        if isinstance(statement, Comment):
            statement_index += 1
            continue

        # Accumulate consecutive Bloch sphere rotations
        if isinstance(statement, BlochSphereRotation):
            already_accumulated = accumulators_per_qubit[statement.qubit]
            composed = compose_bloch_sphere_rotations(statement, already_accumulated)
            accumulators_per_qubit[statement.qubit] = composed
            del circuit.ir.statements[statement_index]
            continue

        def insert_accumulated_bloch_sphere_rotations(qubits: list[Qubit]) -> None:
            nonlocal statement_index
            for qubit in qubits:
                if not accumulators_per_qubit[qubit].is_identity():
                    circuit.ir.statements.insert(statement_index, accumulators_per_qubit[qubit])
                    accumulators_per_qubit[qubit] = I(qubit)
                    statement_index += 1

        # For barrier directives, insert all accumulated Bloch sphere rotations
        # For other instructions, insert accumulated Bloch sphere rotations on qubits used by those instructions
        # In any case, reset the dictionary entry for the inserted accumulated Bloch sphere rotations
        if isinstance(statement, Barrier):
            insert_accumulated_bloch_sphere_rotations([Qubit(i) for i in range(circuit.qubit_register_size)])
        else:
            insert_accumulated_bloch_sphere_rotations(statement.get_qubit_operands())
        statement_index += 1

    for accumulated_bloch_sphere_rotation in accumulators_per_qubit.values():
        if not accumulated_bloch_sphere_rotation.is_identity():
            if accumulated_bloch_sphere_rotation.is_anonymous:
                accumulated_bloch_sphere_rotation = try_name_anonymous_bloch(accumulated_bloch_sphere_rotation)
            circuit.ir.statements.append(accumulated_bloch_sphere_rotation)
