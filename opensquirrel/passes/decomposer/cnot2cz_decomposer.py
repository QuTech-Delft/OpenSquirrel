from __future__ import annotations

from math import pi
from typing import TYPE_CHECKING

from opensquirrel import CZ, Ry
from opensquirrel.ir.semantics import BlochSphereRotation, ControlledGate
from opensquirrel.passes.decomposer.general_decomposer import Decomposer

if TYPE_CHECKING:
    from opensquirrel.ir import Gate


class CNOT2CZDecomposer(Decomposer):
    """Predefined decomposition of CNOT gate to CZ gate with Y rotations.

    ---•---     -----------------•----------------
       |     →                   |
    ---⊕---     --[Ry(-pi/2)]---[Z]---[Ry(pi/2)]--

    Note:
        This decomposition preserves the global phase of the CNOT gate.
    """

    def decompose(self, gate: Gate) -> list[Gate]:
        if gate.name != "CNOT":
            return [gate]
        if isinstance(gate, ControlledGate):
            if not isinstance(gate.target_gate, BlochSphereRotation):
                # ControlledGate's with 2+ control qubits are ignored.
                return [gate]
            control_qubit = gate.control_qubit
            target_qubit = gate.target_gate.qubit
        else:
            # If CNOT is not implemented as a ControlledGate but, e.g., as a MatrixGate.
            control_qubit, target_qubit = gate.get_qubit_operands()
        return [
            Ry(target_qubit, -pi / 2),
            CZ(control_qubit, target_qubit),
            Ry(target_qubit, pi / 2),
        ]
