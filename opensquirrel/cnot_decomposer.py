import math

from opensquirrel import merger
from opensquirrel.common import ATOL
from opensquirrel.default_gates import cnot, ry, rz, x
from opensquirrel.identity_filter import filter_out_identities
from opensquirrel.replacer import Decomposer
from opensquirrel.squirrel_ir import BlochSphereRotation, ControlledGate, Float, Gate
from opensquirrel.zyz_decomposer import ZYZDecomposer, get_zyz_decomposition_angles


class CNOTDecomposer(Decomposer):
    """
    Decomposes 2-qubit controlled unitary gates to CNOT + rz/ry.
    Applying single-qubit gate fusion after this pass might be beneficial.

    Source of the math: https://threeplusone.com/pubs/on_gates.pdf, chapter 7.5 "ABC decomposition"
    """

    @staticmethod
    def decompose(g: Gate) -> [Gate]:
        if not isinstance(g, ControlledGate):
            # Do nothing:
            # - BlochSphereRotation's are only single-qubit,
            # - decomposing MatrixGate is currently not supported.
            return [g]

        if not isinstance(g.target_gate, BlochSphereRotation):
            # Do nothing.
            # ControlledGate's with 2+ control qubits are ignored.
            return [g]

        target_qubit = g.target_gate.qubit

        # Perform ZYZ decomposition on the target gate.
        # This gives us an ABC decomposition (U = AXBXC, ABC = I) of the target gate.
        # See https://threeplusone.com/pubs/on_gates.pdf

        # Try special case first, see https://arxiv.org/pdf/quant-ph/9503016.pdf lemma 5.5
        controlled_rotation_times_x = merger.compose_bloch_sphere_rotations(x(target_qubit), g.target_gate)
        theta0_with_x, theta1_with_x, theta2_with_x = get_zyz_decomposition_angles(
            controlled_rotation_times_x.angle, controlled_rotation_times_x.axis
        )
        if abs((theta0_with_x - theta2_with_x) % (2 * math.pi)) < ATOL:
            # The decomposition can use a single CNOT according to the lemma.

            A = [ry(q=target_qubit, theta=Float(-theta1_with_x / 2)), rz(q=target_qubit, theta=Float(-theta2_with_x))]

            B = [
                rz(q=target_qubit, theta=Float(theta2_with_x)),
                ry(q=target_qubit, theta=Float(theta1_with_x / 2)),
            ]

            return filter_out_identities(
                B
                + [cnot(control=g.control_qubit, target=target_qubit)]
                + A
                + [rz(q=g.control_qubit, theta=Float(g.target_gate.phase - math.pi / 2))]
            )

        theta0, theta1, theta2 = get_zyz_decomposition_angles(g.target_gate.angle, g.target_gate.axis)

        A = [ry(q=target_qubit, theta=Float(theta1 / 2)), rz(q=target_qubit, theta=Float(theta2))]

        B = [
            rz(q=target_qubit, theta=Float(-(theta0 + theta2) / 2)),
            ry(q=target_qubit, theta=Float(-theta1 / 2)),
        ]

        C = [
            rz(q=target_qubit, theta=Float((theta0 - theta2) / 2)),
        ]

        return filter_out_identities(
            C
            + [cnot(control=g.control_qubit, target=target_qubit)]
            + B
            + [cnot(control=g.control_qubit, target=target_qubit)]
            + A
            + [rz(q=g.control_qubit, theta=Float(g.target_gate.phase))]
        )
