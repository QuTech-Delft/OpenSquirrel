from __future__ import annotations

import copy
from math import acos, cos, floor, log10, sin
from typing import TYPE_CHECKING, Any

import numpy as np

from opensquirrel.common import ATOL
from opensquirrel.default_gates import I, default_bloch_sphere_rotations_without_params
from opensquirrel.ir import Barrier, BlochSphereRotation, Comment, Qubit, Statement
from opensquirrel.utils.list import flatten_irregular_list, flatten_list

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


def merge_barriers(statement_list: list[Statement]) -> list[Statement]:
    """Receives a list of statements.
    Returns an ordered version of the input list of statements where groups of barriers are merged together,
    and placed as late in the list as possible.

    Args:
        statement_list: list of statements

    Returns:
        Statement list with the barriers merged.
    """
    barrier_list: list[Barrier] = []
    ordered_statement_list: list[Statement] = []
    for statement in statement_list:
        if isinstance(statement, Comment):
            continue
        if isinstance(statement, Barrier):
            barrier_list.append(statement)
        else:
            if len(barrier_list) > 0 and hasattr(statement, "get_qubit_operands"):
                instruction_qubits = statement.get_qubit_operands()
                barrier_qubits = flatten_list([barrier.get_qubit_operands() for barrier in barrier_list])
                if any(qubit in barrier_qubits for qubit in instruction_qubits):
                    ordered_statement_list.extend(barrier_list)
                    barrier_list = []
            ordered_statement_list.append(statement)

    if len(barrier_list) > 0:
        ordered_statement_list.extend(barrier_list)

    return ordered_statement_list


def sticky_barriers(initial_circuit: list[Statement], current_circuit: list[Statement]) -> list[Statement]:
    """This process takes the initial circuit inputted by the user and joins the barriers that were originally
    placed together before the single qubit gate merge.

    Args:
        initial_circuit: The original order of the statement list
        current_circuit: The current order of the statement list

    Returns:
        List of statements with the respected original barrier positions
    """
    barrier_groups: list[list[Barrier]] = []
    local_group = []
    modified_circuit: list[Any] = copy.deepcopy(current_circuit)

    for i, statement in enumerate(initial_circuit):
        if isinstance(statement, Barrier):
            local_group.append(statement)
        elif len(local_group) > 0:
            barrier_groups.append(local_group)
            local_group = []
        if len(local_group) > 0 and i + 1 == len(initial_circuit):
            barrier_groups.append(local_group)
            local_group = []

    group_counter = 0
    placement_counter = 0
    if len(barrier_groups) > 0:
        for i, statement in enumerate(modified_circuit):
            if placement_counter != 0:
                placement_counter -= 1
                continue
            if barrier_groups[group_counter][-1] == statement:
                del modified_circuit[i]
                modified_circuit.insert(i, barrier_groups[group_counter])
                placement_counter = len(barrier_groups[group_counter])
                group_counter += 1

            elif isinstance(statement, Barrier):
                modified_circuit[i] = None

        modified_circuit = [statement for statement in modified_circuit if statement is not None]

        modified_circuit = flatten_irregular_list(modified_circuit)

    return modified_circuit


def merge_single_qubit_gates(circuit: Circuit) -> None:
    """Merge all consecutive 1-qubit gates in the circuit.

    Gates obtained from merging other gates become anonymous gates.

    Args:
        circuit: Circuit to perform the merge on.
    """
    accumulators_per_qubit: dict[Qubit, BlochSphereRotation] = {
        Qubit(qubit_index): I(qubit_index) for qubit_index in range(circuit.qubit_register_size)
    }

    ir = circuit.ir
    statement_index = 0
    initial_circuit = copy.deepcopy(circuit.ir.statements)
    while statement_index < len(ir.statements):
        statement = ir.statements[statement_index]

        # Skip, since statement is a comment
        if isinstance(statement, Comment):
            statement_index += 1
            continue

        # Accumulate consecutive Bloch sphere rotations
        if isinstance(statement, BlochSphereRotation):
            already_accumulated = accumulators_per_qubit[statement.qubit]

            composed = compose_bloch_sphere_rotations(statement, already_accumulated)
            accumulators_per_qubit[statement.qubit] = composed

            del ir.statements[statement_index]
            continue

        # For other instructions than Bloch sphere rotations,
        # check if those instructions operate on qubits for which we keep an accumulated Bloch sphere rotation,
        # and, in case they do, insert those corresponding accumulated Bloch sphere rotations
        for qubit_operand in statement.get_qubit_operands():  # type: ignore
            if not accumulators_per_qubit[qubit_operand].is_identity():
                ir.statements.insert(statement_index, accumulators_per_qubit[qubit_operand])
                accumulators_per_qubit[qubit_operand] = I(qubit_operand)
                statement_index += 1

        statement_index += 1

    for accumulated_bloch_sphere_rotation in accumulators_per_qubit.values():
        if not accumulated_bloch_sphere_rotation.is_identity():
            if accumulated_bloch_sphere_rotation.is_anonymous:
                accumulated_bloch_sphere_rotation = try_name_anonymous_bloch(accumulated_bloch_sphere_rotation)
            ir.statements.append(accumulated_bloch_sphere_rotation)

    ir.statements = sticky_barriers(initial_circuit, ir.statements)
