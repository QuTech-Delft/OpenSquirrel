from __future__ import annotations

from math import acos, cos, floor, log10, sin
from typing import TYPE_CHECKING

import numpy as np

from opensquirrel.common import ATOL
from opensquirrel.default_gates import I, default_bloch_sphere_rotations_without_params
from opensquirrel.ir import (
    IR,
    Barrier,
    BlochSphereRotation,
    Comment,
    ControlledGate,
    Gate,
    MatrixGate,
    Qubit,
    Statement,
)

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


def rearrange_barrier(ir: IR, accumulated_barriers: list[Barrier | None]) -> list[Barrier | None]:
    """Function to place the accumulated barriers into a correct logical order
    within the circuit.

    Args:
        ir: the current IR object
        accumulated_barriers: list of barriers currently accumulated

    Returns:
        The list of accumulated barriers.
    """
    reversed_list = ir.statements[::-1]
    for index, statement in enumerate(reversed_list):
        if statement in accumulated_barriers and isinstance(statement, Barrier):
            del reversed_list[index]
            reversed_list.insert(0, statement)
            accumulated_barriers.remove(statement)

    ir.statements = reversed_list[::-1]
    ir.statements = merge_barriers(ir.statements)

    return accumulated_barriers


def merge_barriers(statement_list: list[Statement]) -> list[Statement]:
    """Function to fix the placement of the barriers such that the barriers are
    merged in the circuit. Note that this function requires the barriers to be
    placed in the correct order.

    Args:
        statement_list: list of statements

    Returns:
        Statement list with the barriers merged.
    """
    barrier_list: list[Barrier] = []
    ordered_statement_list: list[Statement] = []
    for _, statement in enumerate(statement_list):
        if len(barrier_list) > 0 and isinstance(statement, Gate):
            barrier_qubits = next(q.get_qubit_operands() for q in barrier_list)[0]
            if barrier_qubits in statement.get_qubit_operands():
                ordered_statement_list.extend(barrier_list)
                barrier_list = []
        if isinstance(statement, Barrier):
            barrier_list.append(statement)
        else:
            ordered_statement_list.append(statement)

    if len(barrier_list) > 0:
        ordered_statement_list.extend(barrier_list)

    return ordered_statement_list


def merge_single_qubit_gates(circuit: Circuit) -> None:  # noqa: C901
    """Merge all consecutive 1-qubit gates in the circuit.

    Gates obtained from merging other gates become anonymous gates.

    Args:
        circuit: Circuit to perform the merge on.
    """
    accumulators_per_qubit: dict[Qubit, BlochSphereRotation] = {
        Qubit(qubit_index): I(qubit_index) for qubit_index in range(circuit.qubit_register_size)
    }

    accumulated_barriers: list[Barrier | None] = []

    ir = circuit.ir
    statement_index = 0
    while statement_index < len(ir.statements):
        statement = ir.statements[statement_index]

        if isinstance(statement, Comment):
            # Skip, since statement is a comment
            statement_index += 1
            continue

        if isinstance(statement, BlochSphereRotation):
            # Accumulate consecutive Bloch sphere rotations
            already_accumulated = accumulators_per_qubit[statement.qubit]

            composed = compose_bloch_sphere_rotations(statement, already_accumulated)
            accumulators_per_qubit[statement.qubit] = composed

            del ir.statements[statement_index]
            continue

        # Skip controlled-gates, measure, reset, and reset accumulator for their qubit operands
        for qubit_operand in statement.get_qubit_operands():  # type: ignore
            if not accumulators_per_qubit[qubit_operand].is_identity():
                ir.statements.insert(statement_index, accumulators_per_qubit[qubit_operand])
                accumulators_per_qubit[qubit_operand] = I(qubit_operand)
                if (
                    isinstance(statement, MatrixGate)
                    or isinstance(statement, ControlledGate)
                    and len(accumulated_barriers) > 0
                ):
                    qubit_operands = statement.get_qubit_operands()
                    barrier_qubits = next(q.get_qubit_operands() for q in accumulated_barriers if (q is not None))
                    if any(q in barrier_qubits for q in qubit_operands):
                        accumulated_barriers = rearrange_barrier(ir, accumulated_barriers)

                if isinstance(statement, Barrier):
                    if statement in accumulated_barriers:
                        accumulated_barriers = rearrange_barrier(ir, accumulated_barriers)
                    accumulated_barriers.append(statement)

                ir.statements = merge_barriers(ir.statements)
                statement_index += 1

        statement_index += 1

    for accumulated_bloch_sphere_rotation in accumulators_per_qubit.values():
        if not accumulated_bloch_sphere_rotation.is_identity():
            if accumulated_bloch_sphere_rotation.is_anonymous:
                accumulated_bloch_sphere_rotation = try_name_anonymous_bloch(accumulated_bloch_sphere_rotation)
            ir.statements.append(accumulated_bloch_sphere_rotation)
