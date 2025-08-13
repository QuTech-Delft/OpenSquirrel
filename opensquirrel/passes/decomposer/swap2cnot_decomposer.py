from __future__ import annotations

from typing import TYPE_CHECKING

from opensquirrel import CNOT
from opensquirrel.passes.decomposer.general_decomposer import Decomposer

if TYPE_CHECKING:
    from opensquirrel.ir import Gate


class SWAP2CNOTDecomposer(Decomposer):
    """Predefined decomposition of SWAP gate to 3 CNOT gates.
    ---x---     ----•---[X]---•----
       |     →      |    |    |
    ---x---     ---[X]---•---[X]---
    Note:
        This decomposition preserves the global phase of the SWAP gate.
    """

    def decompose(self, gate: Gate) -> list[Gate]:
        if gate.name != "SWAP":
            return [gate]
        qubit0, qubit1 = gate.get_qubit_operands()
        return [
            CNOT(qubit0, qubit1),
            CNOT(qubit1, qubit0),
            CNOT(qubit0, qubit1),
        ]
