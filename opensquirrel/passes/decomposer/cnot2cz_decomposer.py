from __future__ import annotations

from math import pi

from opensquirrel import CZ, Ry
from opensquirrel.ir import Gate
from opensquirrel.passes.decomposer.general_decomposer import Decomposer


class CNOT2CZDecomposer(Decomposer):
    def decompose(self, instruction: Gate) -> list[Gate]:
        """Predefined decomposition of CNOT gate into CZ gate with Ry rotations.

        ![image](../../../_static/cnot2cz.png#only-light)
        ![image](../../../_static/cnot2cz_dm.png#only-dark)

        Note:
            This decomposition preserves the global phase of the CNOT gate.

        Args:
            instruction (Instruction): CNOT gate to decompose.

        Returns:
            A sequence of gates, Ry(-π/2)-CZ-Ry(π/2), that decompose the CNOT gate.

        """
        if not isinstance(instruction, Gate) or instruction.name != "CNOT":
            return [instruction]

        gate = instruction
        control_qubit, target_qubit = gate.qubit_operands
        return [
            Ry(target_qubit, -pi / 2),
            CZ(control_qubit, target_qubit),
            Ry(target_qubit, pi / 2),
        ]
