from __future__ import annotations

from math import pi
from typing import TYPE_CHECKING

import numpy as np

from opensquirrel import CNOT, CZ, X90, H, MinusX90, Ry, S, SDagger, Z
from opensquirrel.ir.semantics.bsr import BlochSphereRotation
from opensquirrel.ir.single_qubit_gate import SingleQubitGate
from opensquirrel.ir.two_qubit_gate import TwoQubitGate
from opensquirrel.passes.decomposer.general_decomposer import Decomposer

if TYPE_CHECKING:
    from opensquirrel.ir import Gate


class Can2CZDecomposer(Decomposer):
    def decompose(self, instruction: Gate) -> list[Gate]:
        """General decomposition of an arbitrary 2-qubit gate into (at most 3) CZ gate(s) with single-qubit rotations.

        Adapted from [Quantum Gates by G.E. Crooks (2024), Section 7.3](https://threeplusone.com/pubs/on_gates.pdf).

        Note:
            This decomposition does not, in general, preserve the global phase of the original gate.
            It is advised to run the single-qubit gates merger pass after this decomposition pass.

        Args:
            instruction (Gate): 2-qubit gate to decompose.

        Returns:
            Decomposition of the original gate into a sequence of gates.

        """
        if not isinstance(instruction, TwoQubitGate):
            return [instruction]

        gate = instruction
        q0, q1 = gate.qubit_operands

        if gate == CZ(q0, q1):
            return [gate]

        if gate == CNOT(q0, q1):
            return [Ry(q1, -pi / 2), CZ(q0, q1), Ry(q1, pi / 2)]

        # Canonical 4x4 factors follow tensor-product order (higher index first).
        q0, q1 = (q0, q1) if q0.index > q1.index else (q1, q0)

        gate_axis = gate.canonical.axis
        gate_rotations = gate.canonical.rotations
        if gate_rotations is None:
            gate_rotations = [BlochSphereRotation(axis=(1, 0, 0), angle=0, phase=0)] * 4
        k1 = SingleQubitGate(q0, gate_rotations[0])
        k2 = SingleQubitGate(q1, gate_rotations[1])
        k3 = SingleQubitGate(q0, gate_rotations[2])
        k4 = SingleQubitGate(q1, gate_rotations[3])

        if np.allclose(gate_axis.value, np.array([0.5, 0, 0])):
            return [
                k1,
                k2,
                H(q0),
                S(q0),
                H(q1),
                S(q1),
                H(q1),
                Ry(q1, -pi / 2),
                CZ(q0, q1),
                Ry(q1, pi / 2),
                H(q0),
                k3,
                k4,
            ]
        if np.isclose(gate_axis.value[2], 0):
            tx, ty, _ = gate_axis.value
            Xtx = SingleQubitGate(q0, BlochSphereRotation(axis=(1, 0, 0), angle=pi * tx, phase=pi / 2 * tx))  # noqa: N806
            Zty = SingleQubitGate(q1, BlochSphereRotation(axis=(0, 0, 1), angle=pi * ty, phase=pi / 2 * ty))  # noqa: N806
            return [
                k1,
                k2,
                Z(q0),
                MinusX90(q0),
                Z(q1),
                MinusX90(q1),
                Ry(q1, -pi / 2),
                CZ(q0, q1),
                Ry(q1, pi / 2),
                Xtx,
                Zty,
                Ry(q1, -pi / 2),
                CZ(q0, q1),
                Ry(q1, pi / 2),
                X90(q0),
                Z(q0),
                X90(q1),
                Z(q1),
                k3,
                k4,
            ]
        tx, ty, tz = gate_axis.value
        ztz = tz - 0.5
        ytx = tx - 0.5
        yty = 0.5 - ty
        Ztz = SingleQubitGate(q0, BlochSphereRotation(axis=(0, 0, 1), angle=pi * ztz, phase=pi / 2 * ztz))  # noqa: N806
        Ytx = SingleQubitGate(q1, BlochSphereRotation(axis=(0, 1, 0), angle=pi * ytx, phase=pi / 2 * ytx))  # noqa: N806
        Yty = SingleQubitGate(q1, BlochSphereRotation(axis=(0, 1, 0), angle=pi * yty, phase=pi / 2 * yty))  # noqa: N806
        return [
            k1,
            k2,
            S(q1),
            Ry(q0, -pi / 2),
            CZ(q1, q0),
            Ry(q0, pi / 2),
            Ztz,
            Ytx,
            Ry(q1, -pi / 2),
            CZ(q0, q1),
            Ry(q1, pi / 2),
            Yty,
            Ry(q0, -pi / 2),
            CZ(q1, q0),
            Ry(q0, pi / 2),
            SDagger(q0),
            k3,
            k4,
        ]
