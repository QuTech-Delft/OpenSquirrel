from math import acos, cos, floor, log10, sin

import numpy as np

from opensquirrel.circuit import Circuit
from opensquirrel.common import ATOL
from opensquirrel.default_gates import I, default_bloch_sphere_rotations_without_params
from opensquirrel.ir import BlochSphereRotation, Comment, Qubit


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


def merge_single_qubit_gates(circuit: Circuit) -> None:
    """Merge all consecutive 1-qubit gates in the circuit.

    Gates obtained from merging other gates become anonymous gates.
    """
    accumulators_per_qubit: dict[Qubit, BlochSphereRotation] = {
        Qubit(qubit_index): I(Qubit(qubit_index)) for qubit_index in range(circuit.qubit_register_size)
    }

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
                statement_index += 1

        statement_index += 1

    for accumulated_bloch_sphere_rotation in accumulators_per_qubit.values():
        if not accumulated_bloch_sphere_rotation.is_identity():
            if accumulated_bloch_sphere_rotation.is_anonymous:
                accumulated_bloch_sphere_rotation = try_name_anonymous_bloch(accumulated_bloch_sphere_rotation)
            ir.statements.append(accumulated_bloch_sphere_rotation)
