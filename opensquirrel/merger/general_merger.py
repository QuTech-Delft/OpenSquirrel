from math import acos, cos, sin

import numpy as np

from opensquirrel.common import ATOL
from opensquirrel.squirrel_ir import BlochSphereRotation, Gate, Measure, Qubit, SquirrelIR


def compose_bloch_sphere_rotations(a: BlochSphereRotation, b: BlochSphereRotation) -> BlochSphereRotation:
    """Computes the Bloch sphere rotation resulting from the composition of two Bloch sphere rotations.
    The first rotation is applied and then the second.
    The resulting gate is anonymous except if `a` is the identity and `b` is not anonymous, or vice versa.

    Uses Rodrigues' rotation formula, see for instance https://en.wikipedia.org/wiki/Rodrigues%27_rotation_formula.
    """
    assert a.qubit == b.qubit, "Cannot merger two BlochSphereRotation's on different qubits"

    acos_argument = cos(a.angle / 2) * cos(b.angle / 2) - sin(a.angle / 2) * sin(b.angle / 2) * np.dot(a.axis, b.axis)
    # This fixes float approximations like 1.0000000000002 which acos doesn't like.
    acos_argument = max(min(acos_argument, 1.0), -1.0)

    combined_angle = 2 * acos(acos_argument)

    if abs(sin(combined_angle / 2)) < ATOL:
        return BlochSphereRotation.identity(a.qubit)

    combined_axis = (
        1
        / sin(combined_angle / 2)
        * (
            sin(a.angle / 2) * cos(b.angle / 2) * a.axis
            + cos(a.angle / 2) * sin(b.angle / 2) * b.axis
            + sin(a.angle / 2) * sin(b.angle / 2) * np.cross(a.axis, b.axis)
        )
    )

    combined_phase = a.phase + b.phase

    generator = b.generator if a.is_identity() else a.generator if b.is_identity() else None
    arguments = b.arguments if a.is_identity() else a.arguments if b.is_identity() else None

    return BlochSphereRotation(
        qubit=a.qubit,
        axis=combined_axis,
        angle=combined_angle,
        phase=combined_phase,
        generator=generator,
        arguments=arguments,
    )


def merge_single_qubit_gates(squirrel_ir: SquirrelIR):
    accumulators_per_qubit: dict[Qubit, BlochSphereRotation] = {
        Qubit(q): BlochSphereRotation.identity(Qubit(q)) for q in range(squirrel_ir.number_of_qubits)
    }

    statement_index = 0
    while statement_index < len(squirrel_ir.statements):
        statement = squirrel_ir.statements[statement_index]

        if not isinstance(statement, Gate) and not isinstance(statement, Measure):
            # Skip, since statement is not a gate or measurement
            statement_index += 1
            continue

        if isinstance(statement, BlochSphereRotation):
            # Accumulate
            already_accumulated = accumulators_per_qubit.get(statement.qubit)

            composed = compose_bloch_sphere_rotations(statement, already_accumulated)
            accumulators_per_qubit[statement.qubit] = composed

            del squirrel_ir.statements[statement_index]
            continue

        for qubit_operand in statement.get_qubit_operands():
            if not accumulators_per_qubit[qubit_operand].is_identity():
                squirrel_ir.statements.insert(statement_index, accumulators_per_qubit[qubit_operand])
                accumulators_per_qubit[qubit_operand] = BlochSphereRotation.identity(qubit_operand)
                statement_index += 1
        statement_index += 1

    for accumulated_bloch_sphere_rotation in accumulators_per_qubit.values():
        if not accumulated_bloch_sphere_rotation.is_identity():
            squirrel_ir.statements.append(accumulated_bloch_sphere_rotation)

    squirrel_ir.statements = sorted(squirrel_ir.statements, key=lambda obj: isinstance(obj, Measure))
