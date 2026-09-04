from __future__ import annotations

from math import pi
from typing import TYPE_CHECKING

from opensquirrel import CZ, Ry, T, TDagger
from opensquirrel.passes.decomposer.general_decomposer import Decomposer

if TYPE_CHECKING:
    from opensquirrel.ir import Gate, Qubit


def _cnot_to_cz(control_qubit: Qubit, target_qubit: Qubit) -> list[Gate]:
    """CNOT expressed as a CZ gate conjugated by Ry rotations, as in the CNOT2CZDecomposer."""
    return [
        Ry(target_qubit, -pi / 2),
        CZ(control_qubit, target_qubit),
        Ry(target_qubit, pi / 2),
    ]


def _ccx_to_cz(control_qubit_0: Qubit, control_qubit_1: Qubit, target_qubit: Qubit) -> list[Gate]:
    """Toffoli gate as 6 CNOT gates and T rotations, with every CNOT gate rewritten in terms of CZ."""
    a, b, c = control_qubit_0, control_qubit_1, target_qubit
    return [
        Ry(c, -pi / 2),
        *_cnot_to_cz(b, c),
        TDagger(c),
        *_cnot_to_cz(a, c),
        T(c),
        *_cnot_to_cz(b, c),
        TDagger(c),
        *_cnot_to_cz(a, c),
        T(b),
        T(c),
        Ry(c, pi / 2),
        *_cnot_to_cz(a, b),
        T(a),
        TDagger(b),
        *_cnot_to_cz(a, b),
    ]


class ThreeQubitGateDecomposer(Decomposer):
    def decompose(self, instruction: Gate) -> list[Gate]:
        """Predefined decomposition of the three-qubit gates into CZ gates and single-qubit gates.

        The Toffoli gate (CCX) is decomposed into 6 CZ gates and single-qubit rotations, which is
        the minimum possible according to
        [Shende and Markov (2008)](https://arxiv.org/abs/0803.2316). The Fredkin gate (CSWAP) is
        decomposed as a Toffoli gate conjugated by two CNOT gates, giving 8 CZ gates.

        Note:
            This decomposition preserves the global phase of the three-qubit gate.
            Gates other than CCX and CSWAP are returned unchanged.

        Args:
            instruction: three-qubit gate to decompose.

        Returns:
            A sequence of CZ gates and single-qubit gates that decompose the three-qubit gate.

        """
        if instruction.name not in ("CCX", "CSWAP"):
            return [instruction]

        gate = instruction

        if gate.name == "CCX":
            control_qubit_0, control_qubit_1, target_qubit = gate.qubit_operands
            return _ccx_to_cz(control_qubit_0, control_qubit_1, target_qubit)

        control_qubit, qubit_0, qubit_1 = gate.qubit_operands
        return [
            *_cnot_to_cz(qubit_1, qubit_0),
            *_ccx_to_cz(control_qubit, qubit_0, qubit_1),
            *_cnot_to_cz(qubit_1, qubit_0),
        ]
