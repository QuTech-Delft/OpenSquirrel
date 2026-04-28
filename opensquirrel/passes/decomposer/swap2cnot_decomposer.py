from __future__ import annotations

from typing import TYPE_CHECKING

from opensquirrel import CNOT
from opensquirrel.passes.decomposer.general_decomposer import Decomposer

if TYPE_CHECKING:
    from opensquirrel.ir import Gate


class SWAP2CNOTDecomposer(Decomposer):
    def decompose(self, instruction: Gate) -> list[Gate]:
        """Predefined decomposition of SWAP gate to 3 CNOT gates.

        ![image](../../../_static/swap2cnot.png#only-light)
        ![image](../../../_static/swap2cnot_dm.png#only-dark)

        Note:
            This decomposition preserves the global phase of the SWAP gate.

        Args:
            instruction: SWAP gate to decompose.

        Returns:
            A sequence of 3 CNOT gates that decompose the SWAP gate.

        """
        if instruction.name != "SWAP":
            return [instruction]

        gate = instruction

        qubit0, qubit1 = gate.qubit_operands
        return [
            CNOT(qubit0, qubit1),
            CNOT(qubit1, qubit0),
            CNOT(qubit0, qubit1),
        ]
