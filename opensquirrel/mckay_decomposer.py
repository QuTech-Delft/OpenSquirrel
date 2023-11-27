from math import acos, atan2, cos, pi, sin, sqrt
from typing import Tuple

import numpy as np

from opensquirrel.common import ATOL, ArgType
from opensquirrel.gates import SingleQubitAxisAngleSemantic, queryEntry, querySemantic, querySignature
from opensquirrel.squirrel_ast import SquirrelAST


def normalizeAngle(x: float) -> float:
    t = x - 2 * pi * (x // (2 * pi) + 1)
    if t < -pi + ATOL:
        t += 2 * pi
    elif t > pi:
        t -= 2 * pi
    return t


class McKayDecomposer:
    def __init__(self, gates):
        self.gates = gates

        queryEntry(self.gates, "rz")  # FIXME: improve. Pass those gates as parameters to the constructor.
        queryEntry(self.gates, "x90")

    def _decomposeAndAdd(self, qubit, angle: float, axis: Tuple[float, float, float]):
        if abs(angle) < ATOL:
            return

        # McKay decomposition

        zaMod = sqrt(cos(angle / 2) ** 2 + (axis[2] * sin(angle / 2)) ** 2)
        zbMod = abs(sin(angle / 2)) * sqrt(axis[0] ** 2 + axis[1] ** 2)

        theta = pi - 2 * atan2(zbMod, zaMod)

        alpha = atan2(-sin(angle / 2) * axis[2], cos(angle / 2))
        beta = atan2(-sin(angle / 2) * axis[0], -sin(angle / 2) * axis[1])

        lam = beta - alpha
        phi = -beta - alpha - pi

        lam = normalizeAngle(lam)
        phi = normalizeAngle(phi)
        theta = normalizeAngle(theta)

        if abs(lam) > ATOL:
            self.output.addGate("rz", qubit, lam)

        self.output.addGate("x90", qubit)

        if abs(theta) > ATOL:
            self.output.addGate("rz", qubit, theta)

        self.output.addGate("x90", qubit)

        if abs(phi) > ATOL:
            self.output.addGate("rz", qubit, phi)

    def _flush(self, q):
        if q not in self.oneQubitGates:
            return
        p = self.oneQubitGates.pop(q)
        self._decomposeAndAdd(q, p["angle"], p["axis"])

    def _flush_all(self):
        while len(self.oneQubitGates) > 0:
            self._flush(next(iter(self.oneQubitGates.keys())))

    def _acc(self, qubit, semantic: SingleQubitAxisAngleSemantic):
        axis, angle, phase = semantic.axis, semantic.angle, semantic.phase

        if qubit not in self.oneQubitGates:
            self.oneQubitGates[qubit] = {"angle": angle, "axis": axis, "phase": phase}
            return

        existing = self.oneQubitGates[qubit]
        combinedPhase = phase + existing["phase"]

        a = angle
        l = axis
        b = existing["angle"]
        m = existing["axis"]

        combinedAngle = 2 * acos(cos(a / 2) * cos(b / 2) - sin(a / 2) * sin(b / 2) * np.dot(l, m))

        if abs(sin(combinedAngle / 2)) < ATOL:
            self.oneQubitGates.pop(qubit)
            return

        combinedAxis = (
            1
            / sin(combinedAngle / 2)
            * (sin(a / 2) * cos(b / 2) * l + cos(a / 2) * sin(b / 2) * m + sin(a / 2) * sin(b / 2) * np.cross(l, m))
        )

        self.oneQubitGates[qubit] = {"angle": combinedAngle, "axis": combinedAxis, "phase": combinedPhase}

    def process(self, squirrelAST):
        # FIXME: duplicate gates in ast and self??
        self.output = SquirrelAST(self.gates, squirrelAST.nQubits, squirrelAST.qubitRegisterName)
        self.oneQubitGates = {}

        for operation in squirrelAST.operations:
            if isinstance(operation, str):
                continue

            self._processSingleOperation(operation)

        self._flush_all()

        return self.output  # FIXME: instead of returning a new AST, modify existing one

    def _processSingleOperation(self, operation):
        gateName, gateArgs = operation

        signature = querySignature(self.gates, gateName)
        qubitArguments = [gateArgs[i] for i in range(len(gateArgs)) if signature[i] == ArgType.QUBIT]
        nonQubitArguments = [gateArgs[i] for i in range(len(gateArgs)) if signature[i] != ArgType.QUBIT]

        if len(qubitArguments) >= 2:
            [self._flush(q) for q in qubitArguments]
            self.output.addGate(gateName, *gateArgs)
            return

        if len(qubitArguments) == 0:
            assert False, "Unsupported"
            return

        semantic = querySemantic(self.gates, gateName, *nonQubitArguments)

        assert isinstance(
            semantic, SingleQubitAxisAngleSemantic
        ), f"Not supported for single qubit gate `{gateName}`: {type(semantic)}"

        self._acc(qubitArguments[0], semantic)
