from __future__ import annotations

import math

from opensquirrel.common import ATOL
from opensquirrel.decomposer.aba_decomposer import ZYZDecomposer
from opensquirrel.decomposer.general_decomposer import Decomposer
from opensquirrel.default_gates import H, Z, H, X, GateKind
from opensquirrel.ir import BlochSphereRotation, ControlledGate, Float, Gate
from opensquirrel.merger import general_merger
from opensquirrel.utils.identity_filter import filter_out_identities
from opensquirrel.decomposer.general_decomposer import Decomposer


class TwoQubitGateFolder(Decomposer):
    def uses_multi_gate_replacement(self):
        return True

    def remove_predecessor_gates(self) -> List[int]:
        return [-1]

    def remove_successor_gates(self) -> List[int]:
        return [1]

    def decompose(self, g: Gate, gates_before: list[Statement] = [], gates_after: list[Statement] = []) -> list[Gate]:
        if g.gatekind is GateKind.Z:
            """
            Decomposes 2-qubit H.Z.H to X gate.
            """
            try:
                if gates_before[-1].gatekind is GateKind.H and gates_after[0].gatekind is GateKind.H:
                    return [X(g.get_qubit_operands()[0])]
            except Exception as _:
                pass
        return [g]
