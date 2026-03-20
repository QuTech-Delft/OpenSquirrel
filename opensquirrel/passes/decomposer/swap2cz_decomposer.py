from __future__ import annotations

from math import pi
from typing import TYPE_CHECKING

from opensquirrel import CZ, Ry
from opensquirrel.passes.decomposer.general_decomposer import Decomposer

if TYPE_CHECKING:
    from opensquirrel.ir import Gate


class SWAP2CZDecomposer(Decomposer):
    def decompose(self, instruction: Gate) -> list[Gate]:
        """Predefined decomposition of SWAP gate to 3 CZ gates and Ry rotations.

        ![image](../../../_static/swap2cz.png#only-light)
        ![image](../../../_static/swap2cz_dm.png#only-dark)

        Note:
            This decomposition preserves the global phase of the SWAP gate.

        Args:
            instruction: SWAP gate to decompose.

        Returns:
            A sequence of 3 CZ gates and Ry rotations that decompose the SWAP gate.

        """
        if instruction.name != "SWAP":
            return [instruction]

        gate = instruction

        qubit0, qubit1 = gate.qubit_operands
        return [
            Ry(qubit1, -pi / 2),
            CZ(qubit0, qubit1),
            Ry(qubit1, pi / 2),
            Ry(qubit0, -pi / 2),
            CZ(qubit1, qubit0),
            Ry(qubit0, pi / 2),
            Ry(qubit1, -pi / 2),
            CZ(qubit0, qubit1),
            Ry(qubit1, pi / 2),
        ]
