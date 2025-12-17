from __future__ import annotations

from math import pi
from typing import TYPE_CHECKING

from opensquirrel import CNOT, Ry, Rz, X
from opensquirrel.common import ATOL
from opensquirrel.ir.two_qubit_gate import TwoQubitGate
from opensquirrel.passes.decomposer import ZYZDecomposer
from opensquirrel.passes.decomposer.general_decomposer import Decomposer
from opensquirrel.utils.identity_filter import filter_out_identities

if TYPE_CHECKING:
    from opensquirrel.ir import Gate


class CNOTDecomposer(Decomposer):
    """
    Decomposes 2-qubit controlled unitary gates to CNOT + Rz/Ry.
    Applying single-qubit gate fusion after this pass might be beneficial.

    Source of the math: https://threeplusone.com/pubs/on_gates.pdf, chapter 7.5 "ABC decomposition"
    """

    def decompose(self, g: Gate) -> list[Gate]:
        if not isinstance(g, TwoQubitGate):
            return [g]

        if g.control is None:
            # Do nothing, this is not a controlled unitary gate.
            return [g]

        control_qubit = g.qubit0
        target_qubit = g.qubit1
        target_gate = g.control.target_gate

        # Perform ZYZ decomposition on the target gate.
        # This gives us an ABC decomposition (U = AXBXC, ABC = I) of the target gate.
        # See https://threeplusone.com/pubs/on_gates.pdf

        # Try special case first, see https://arxiv.org/pdf/quant-ph/9503016.pdf lemma 5.5
        controlled_rotation_times_x = target_gate * X(target_qubit)
        theta0_with_x, theta1_with_x, theta2_with_x = ZYZDecomposer().get_decomposition_angles(
            controlled_rotation_times_x.bsr.axis,
            controlled_rotation_times_x.bsr.angle,
        )
        if abs((theta0_with_x - theta2_with_x) % (2 * pi)) < ATOL:
            # The decomposition can use a single CNOT according to the lemma.
            A = [Ry(target_qubit, -theta1_with_x / 2), Rz(target_qubit, -theta2_with_x)]  # noqa: N806
            B = [Rz(target_qubit, theta2_with_x), Ry(target_qubit, theta1_with_x / 2)]  # noqa: N806
            return filter_out_identities(
                [
                    *B,
                    CNOT(control_qubit, target_qubit),
                    *A,
                    Rz(control_qubit, target_gate.bsr.phase - pi / 2),
                ],
            )

        theta0, theta1, theta2 = ZYZDecomposer().get_decomposition_angles(target_gate.bsr.axis, target_gate.bsr.angle)

        A = [Ry(target_qubit, theta1 / 2), Rz(target_qubit, theta2)]  # noqa: N806
        B = [Rz(target_qubit, -(theta0 + theta2) / 2), Ry(target_qubit, -theta1 / 2)]  # noqa: N806
        C = [Rz(target_qubit, (theta0 - theta2) / 2)]  # noqa: N806

        return filter_out_identities(
            [
                *C,
                CNOT(control_qubit, target_qubit),
                *B,
                CNOT(control_qubit, target_qubit),
                *A,
                Rz(control_qubit, target_gate.bsr.phase),
            ],
        )
