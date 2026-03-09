from __future__ import annotations

from math import pi
from typing import TYPE_CHECKING

from opensquirrel import CZ, Ry
from opensquirrel.passes.decomposer.general_decomposer import Decomposer

if TYPE_CHECKING:
    from opensquirrel.ir import Gate


class CNOT2CZDecomposer(Decomposer):
    def decompose(self, gate: Gate) -> list[Gate]:
        """Predefined decomposition of CNOT gate into CZ gate with Ry rotations.

        ![image](../../../_static/cnot2cz.png#only-light)
        ![image](../../../_static/cnot2cz_dm.png#only-dark)

        Note:
            This decomposition preserves the global phase of the CNOT gate.

        Args:
            gate (Gate): CNOT gate to decompose.

        Returns:
            A sequence of gates, Ry(-π/2)-CZ-Ry(π/2), that decompose the CNOT gate.

        """
        if gate.name != "CNOT":
            return [gate]

        control_qubit, target_qubit = gate.qubit_operands
        return [
            Ry(target_qubit, -pi / 2),
            CZ(control_qubit, target_qubit),
            Ry(target_qubit, pi / 2),
        ]
