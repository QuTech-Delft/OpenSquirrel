from __future__ import annotations

from math import pi

from opensquirrel import CZ, Ry
from opensquirrel.ir import Gate
from opensquirrel.passes.decomposer.general_decomposer import Decomposer


class CNOT2CZDecomposer(Decomposer):
    def decompose(self, instruction: Gate) -> list[Gate]:
        """General decomposition of a 2-qubit gate into (at most 3) CZ gate(s) with single-qubit rotations.

        Note:
            This decomposition does not, in general, preserve the global phase of the original gate.

        Args:
            instruction (Gate): 2-qubit gate to decompose.

        Returns:
            Decomposition of the original gate into a sequence of gates.

        """
        if not isinstance(instruction, Gate):
            return [instruction]

        gate = instruction
        q0, q1 = gate.qubit_operands
        return [
            Ry(q1, -pi / 2),
            CZ(q0, q1),
            Ry(q1, pi / 2),
        ]
