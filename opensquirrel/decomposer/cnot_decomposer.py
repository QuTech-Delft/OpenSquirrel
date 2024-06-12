import math

from opensquirrel.common import ATOL
from opensquirrel.decomposer.general_decomposer import Decomposer
from opensquirrel.decomposer.zyz_decomposer import ZYZDecomposer
from opensquirrel.default_gates import CNOT, Ry, Rz, X
from opensquirrel.ir import BlochSphereRotation, ControlledGate, Float, Gate
from opensquirrel.merger import general_merger
from opensquirrel.utils.identity_filter import filter_out_identities


class CNOTDecomposer(Decomposer):
    """
    Decomposes 2-qubit controlled unitary gates to CNOT + Rz/Ry.
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
        controlled_rotation_times_x = general_merger.compose_bloch_sphere_rotations(X(target_qubit), g.target_gate)
        theta0_with_x, theta1_with_x, theta2_with_x = ZYZDecomposer().get_decomposition_angles(
            controlled_rotation_times_x.angle, controlled_rotation_times_x.axis
        )
        if abs((theta0_with_x - theta2_with_x) % (2 * math.pi)) < ATOL:
            # The decomposition can use a single CNOT according to the lemma.

            A = [Ry(q=target_qubit, theta=Float(-theta1_with_x / 2)), Rz(q=target_qubit, theta=Float(-theta2_with_x))]

            B = [
                Rz(q=target_qubit, theta=Float(theta2_with_x)),
                Ry(q=target_qubit, theta=Float(theta1_with_x / 2)),
            ]

            return filter_out_identities(
                B
                + [CNOT(control=g.control_qubit, target=target_qubit)]
                + A
                + [Rz(q=g.control_qubit, theta=Float(g.target_gate.phase - math.pi / 2))]
            )

        theta0, theta1, theta2 = ZYZDecomposer().get_decomposition_angles(g.target_gate.angle, g.target_gate.axis)

        A = [Ry(q=target_qubit, theta=Float(theta1 / 2)), Rz(q=target_qubit, theta=Float(theta2))]

        B = [
            Rz(q=target_qubit, theta=Float(-(theta0 + theta2) / 2)),
            Ry(q=target_qubit, theta=Float(-theta1 / 2)),
        ]

        C = [
            Rz(q=target_qubit, theta=Float((theta0 - theta2) / 2)),
        ]

        return filter_out_identities(
            C
            + [CNOT(control=g.control_qubit, target=target_qubit)]
            + B
            + [CNOT(control=g.control_qubit, target=target_qubit)]
            + A
            + [Rz(q=g.control_qubit, theta=Float(g.target_gate.phase))]
        )
