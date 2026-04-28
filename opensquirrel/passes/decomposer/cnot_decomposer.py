from __future__ import annotations

from math import pi
from typing import TYPE_CHECKING

from opensquirrel import CNOT, Ry, Rz, X
from opensquirrel.common import ATOL
from opensquirrel.ir.single_qubit_gate import SingleQubitGate
from opensquirrel.ir.two_qubit_gate import TwoQubitGate
from opensquirrel.passes.decomposer import ZYZDecomposer
from opensquirrel.passes.decomposer.general_decomposer import Decomposer
from opensquirrel.utils.identity_filter import filter_out_identities

if TYPE_CHECKING:
    from opensquirrel.ir import Gate


class CNOTDecomposer(Decomposer):
    """Decomposes 2-qubit controlled unitary gates to CNOT + Rz/Ry.

    Applying single-qubit gate fusion after this pass might be beneficial.

    Based on the CNOT decomposition described in
    [Quantum Gates by G.E. Crooks (2024), Section 7.5](https://threeplusone.com/pubs/on_gates.pdf).
    """

    def decompose(self, instruction: Gate) -> list[Gate]:
        """Decomposes a controlled two-qubit gate into a sequence of (at most 2) CNOT gates and
        single-qubit gates. It decomposes the CR, CRk, and CZ controlled two-qubit gates.

        Note:
            The SWAP gate is not a controlled two-qubit gate and is not decomposed by this pass.
            To decompose SWAP gates, use the
            [SWAP2CNOTDecomposer][opensquirrel.passes.decomposer.swap2cnot_decomposer.SWAP2CNOTDecomposer]
            or the [SWAP2CZDecomposer][opensquirrel.passes.decomposer.swap2cz_decomposer.SWAP2CZDecomposer].

        Args:
            instruction (Instruction): Two-qubit controlled gate to decompose.

        Returns:
            A sequence of (at most 2) CNOT gates and single-qubit gates.

        """
        if not isinstance(instruction, TwoQubitGate):
            return [instruction]
        gate = instruction

        if not gate.controlled:
            return [gate]

        control_qubit = gate.qubit0
        target_qubit = gate.qubit1
        target_gate = SingleQubitGate(qubit=target_qubit, gate_semantic=gate.controlled.target_bsr)
        # Perform ZYZ decomposition on the target gate.
        # This gives us an ABC decomposition (U = AXBXC, ABC = I) of the target gate.
        # See https://threeplusone.com/pubs/on_gates.pdf

        # Try special case first, see https://arxiv.org/pdf/quant-ph/9503016.pdf lemma 5.5
        controlled_rotation_times_x = target_gate * X(target_qubit)
        theta0_with_x, theta1_with_x, theta2_with_x = ZYZDecomposer()._determine_rotation_angles(  # noqa: SLF001
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

        theta0, theta1, theta2 = ZYZDecomposer()._determine_rotation_angles(target_gate.bsr.axis, target_gate.bsr.angle)  # noqa: SLF001

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
