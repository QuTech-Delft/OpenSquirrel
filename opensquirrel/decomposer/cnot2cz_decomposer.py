from __future__ import annotations

import math

from opensquirrel.decomposer import Decomposer
from opensquirrel.default_gates import CZ, Ry
from opensquirrel.ir import BlochSphereRotation, Gate, ControlledGate, Float


class CNOT2CZDecomposer(Decomposer):
    """Predefined decomposition of CNOT gate to CZ gate with Y rotations.

    ---•---     -----------------•----------------
       |     →                   |
    ---⊕---     --[Ry(-pi/2)]---[Z]---[Ry(pi/2)]--

    This decomposition preserves the global phase.

    """
    def decompose(self, gate: Gate) -> list[Gate]:
        if not gate.name == "CNOT" and not isinstance(gate, ControlledGate):
            # Do nothing, also if CNOT is represented as a Matrix.
            return [gate]
        else:
            if not isinstance(gate.target_gate, BlochSphereRotation):
                # Do nothing.
                # ControlledGate's with 2+ control qubits are ignored.
                return [gate]

            control_qubit = gate.control_qubit
            target_qubit = gate.target_gate.qubit

            return [
                Ry(target_qubit, Float(-math.pi/2)),
                CZ(control_qubit, target_qubit),
                Ry(target_qubit, Float(math.pi/2)),
            ]
