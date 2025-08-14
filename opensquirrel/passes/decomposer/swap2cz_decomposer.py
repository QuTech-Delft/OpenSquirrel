from __future__ import annotations

from math import pi
from typing import TYPE_CHECKING

from opensquirrel import CZ, Ry
from opensquirrel.passes.decomposer.general_decomposer import Decomposer

if TYPE_CHECKING:
    from opensquirrel.ir import Gate


class SWAP2CZDecomposer(Decomposer):
    """Predefined decomposition of SWAP gate to Ry rotations and 3 CZ gates.
    ---x---     -------------•-[Ry(-pi/2)]-•-[Ry(+pi/2)]-•-------------
       |     →               |             |             |
    ---x---     -[Ry(-pi/2)]-•-[Ry(+pi/2)]-•-[Ry(-pi/2)]-•-[Ry(+pi/2)]-
    Note:
        This decomposition preserves the global phase of the SWAP gate.
    """

    def decompose(self, gate: Gate) -> list[Gate]:
        if gate.name != "SWAP":
            return [gate]
        qubit0, qubit1 = gate.get_qubit_operands()
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
