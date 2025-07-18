from __future__ import annotations

import math

import numpy as np

from opensquirrel import Circuit, CircuitBuilder
from opensquirrel.passes.decomposer import CNOT2CZDecomposer, CNOTDecomposer, McKayDecomposer, XYXDecomposer
from opensquirrel.passes.merger import SingleQubitGatesMerger


def test_integration_global_phase() -> None:
    circuit = Circuit.from_string(
        """
        version 3.0
        qubit[3] q
        H q[0:2]
        Ry(1.5789) q[0]
        H q[0]
        CNOT q[1], q[0]
        Ry(3.09) q[0]
        Ry(0.318) q[1]
        Ry(0.18) q[2]
        CNOT q[2], q[0]
        """,
    )

    # Decompose 2-qubit gates to a decomposition where the 2-qubit interactions are captured by CNOT gates
    circuit.decompose(decomposer=CNOTDecomposer())

    # Replace CNOT gates with CZ gates
    circuit.decompose(decomposer=CNOT2CZDecomposer())
    # Merge single-qubit gates and decompose with McKay decomposition.
    circuit.merge(merger=SingleQubitGatesMerger())
    circuit.decompose(decomposer=McKayDecomposer())
    assert (
        str(circuit)
        == """version 3.0

qubit[3] q

Rz(1.5707963) q[1]
X90 q[1]
Rz(1.5707963) q[1]
Rz(3.1415927) q[0]
X90 q[0]
Rz(0.0081036221) q[0]
X90 q[0]
CZ q[1], q[0]
X90 q[2]
Rz(1.3907963) q[2]
X90 q[2]
Rz(3.1415927) q[0]
X90 q[0]
Rz(0.051592654) q[0]
X90 q[0]
CZ q[2], q[0]
Rz(-1.5707963) q[0]
X90 q[0]
Rz(1.5707963) q[0]
Rz(3.1415927) q[1]
X90 q[1]
Rz(2.8235927) q[1]
X90 q[1]
"""
    )


def test_phase_map_circuit_builder() -> None:
    circuit_builder = CircuitBuilder(4)
    circuit_builder.H(0).H(1).H(2).H(3).Rz(0, math.pi / 8).Ry(1, math.pi / 4).Rx(2, 3 * math.pi / 8).Ry(
        3, math.pi / 2
    ).CNOT(1, 2).CNOT(0, 3).Rz(0, math.pi / 8).Ry(1, math.pi / 4).Rx(2, 3 * math.pi / 8).Ry(3, math.pi / 2)
    circuit = circuit_builder.to_circuit()
    circuit.merge(SingleQubitGatesMerger())
    circuit.decompose(XYXDecomposer())
    assert np.allclose(circuit.phase_map.qubit_phase_map, [math.pi / 2, math.pi / 2, -math.pi / 2, math.pi / 2])
