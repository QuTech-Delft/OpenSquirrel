import math

from opensquirrel.common import ATOL
from opensquirrel.default_gates import cnot, ry, rz
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

        # Perform ZYZ decomposition on the target gate.
        # This gives us an ABC decomposition (U = AXBXC, ABC = I) of the target gate.
        # See https://threeplusone.com/pubs/on_gates.pdf
        theta0, theta1, theta2 = get_zyz_decomposition_angles(g.target_gate.angle, g.target_gate.axis)
        target_qubit = g.target_gate.qubit

        # First try to see if we can get away with a single CNOT.
        # FIXME: see https://github.com/QuTech-Delft/OpenSquirrel/issues/99 this could be extended, I believe.
        if abs(abs(theta0 + theta2) % (2 * math.pi)) < ATOL and abs(abs(theta1 - math.pi) % (2 * math.pi)) < ATOL:
            # g == rz(theta0) Y rz(theta2) == rz(theta0 - pi / 2) X rz(theta2 + pi / 2)
            # theta0 + theta2 == 0

            alpha0 = theta0 - math.pi / 2
            alpha2 = theta2 + math.pi / 2

            return filter_out_identities(
                [
                    rz(q=target_qubit, theta=Float(alpha2)),
                    cnot(control=g.control_qubit, target=target_qubit),
                    rz(q=target_qubit, theta=Float(alpha0)),
                    rz(q=g.control_qubit, theta=Float(g.target_gate.phase - math.pi / 2)),
                ]
            )

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
