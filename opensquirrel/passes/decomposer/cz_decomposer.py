from __future__ import annotations

from math import pi
from typing import TYPE_CHECKING

from opensquirrel import CZ, Rx, Ry, Rz, Z
from opensquirrel.common import ATOL
from opensquirrel.ir.semantics import BlochSphereRotation, ControlledGate
from opensquirrel.passes.decomposer import XYXDecomposer
from opensquirrel.passes.decomposer.general_decomposer import Decomposer
from opensquirrel.passes.merger import general_merger
from opensquirrel.utils import filter_out_identities

if TYPE_CHECKING:
    from opensquirrel.ir import Gate


class CZDecomposer(Decomposer):
    """
    Decomposes 2-qubit controlled unitary gates to CZ + Rx/Ry.
    Applying single-qubit gate fusion after this pass might be beneficial.

    Source of the math: https://threeplusone.com/pubs/on_gates.pdf, chapter 7.5 "ABC decomposition"
    """

    def decompose(self, g: Gate) -> list[Gate]:
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

        # Perform XYX decomposition on the target gate.
        # This gives us an ABC decomposition (U = exp(i phase) * AZBZC, ABC = I) of the target gate.
        # See https://threeplusone.com/pubs/on_gates.pdf

        # Try special case first, see https://arxiv.org/pdf/quant-ph/9503016.pdf lemma 5.5
        # Note that here V = Rx(a) * Ry(th) * Rx(a) * Z to create V = AZBZ, with AB = I
        controlled_rotation_times_z = general_merger.compose_bloch_sphere_rotations(g.target_gate, Z(target_qubit))
        theta0_with_z, theta1_with_z, theta2_with_z = XYXDecomposer().get_decomposition_angles(
            controlled_rotation_times_z.axis,
            controlled_rotation_times_z.angle,
        )
        if abs((theta0_with_z - theta2_with_z) % (2 * pi)) < ATOL:
            # The decomposition can use a single CZ according to the lemma.
            A = [Ry(target_qubit, theta1_with_z / 2), Rx(target_qubit, theta2_with_z)]  # noqa: N806
            B = [Rx(target_qubit, -theta2_with_z), Ry(target_qubit, -theta1_with_z / 2)]  # noqa: N806
            return filter_out_identities(
                [
                    *B,
                    CZ(g.control_qubit, target_qubit),
                    *A,
                    Rz(g.control_qubit, g.target_gate.phase - pi / 2),
                ],
            )

        theta0, theta1, theta2 = XYXDecomposer().get_decomposition_angles(g.target_gate.axis, g.target_gate.angle)

        A = [Ry(target_qubit, theta1 / 2), Rx(target_qubit, theta2)]  # noqa: N806
        B = [Rx(target_qubit, -(theta0 + theta2) / 2), Ry(target_qubit, -theta1 / 2)]  # noqa: N806
        C = [Rx(target_qubit, (theta0 - theta2) / 2)]  # noqa: N806

        return filter_out_identities(
            [
                *C,
                CZ(g.control_qubit, target_qubit),
                *B,
                CZ(g.control_qubit, target_qubit),
                *A,
                Rz(g.control_qubit, g.target_gate.phase),
            ],
        )
