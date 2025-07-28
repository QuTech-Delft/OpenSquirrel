from __future__ import annotations

import math

import numpy as np

from opensquirrel import Circuit, CircuitBuilder
from opensquirrel.passes.decomposer import CNOT2CZDecomposer, CNOTDecomposer, XYXDecomposer
from opensquirrel.passes.merger import SingleQubitGatesMerger


def test_high_level_integration_global_phase() -> None:
    circuit = Circuit.from_string(
        """version 3.0

        qubit[2] q

        H q[0:1]
        CNOT q[1], q[0]
        Ry(3.09) q[0]
        Ry(0.318) q[1]
        CNOT q[1], q[0]
        """,
    )

    # Decompose 2-qubit gates to a decomposition where the 2-qubit interactions are captured by CNOT gates
    circuit.decompose(decomposer=CNOTDecomposer())

    # Replace CNOT gates with CZ gates
    circuit.decompose(decomposer=CNOT2CZDecomposer())
    # Merge single-qubit gates and decompose with McKay decomposition.
    circuit.merge(merger=SingleQubitGatesMerger())
    circuit.decompose(decomposer=XYXDecomposer())
    assert (
        str(circuit)
        == """version 3.0

qubit[2] q

Ry(1.5707963) q[1]
Rx(3.1415927) q[1]
Rx(-1.5707963) q[0]
Ry(3.1415927) q[0]
Rx(1.5707963) q[0]
CZ q[1], q[0]
Ry(0.318) q[1]
Rx(3.1415927) q[0]
Ry(-3.09) q[0]
Rx(-3.1415927) q[0]
CZ q[1], q[0]
Rz(3.1415927) q[1]
Ry(1.5707963) q[0]
"""
    )


def test_phase_record_circuit_builder() -> None:
    circuit_builder = CircuitBuilder(4)
    circuit_builder.H(0).H(1).H(2).H(3).Rz(0, math.pi / 8).Ry(1, math.pi / 4).Rx(2, 3 * math.pi / 8).Ry(
        3, math.pi / 2
    ).CNOT(1, 2).CNOT(0, 3).Rz(0, math.pi / 8).Ry(1, math.pi / 4).Rx(2, 3 * math.pi / 8).Ry(3, math.pi / 2).CNOT(
        3, 1
    ).CNOT(2, 0).Rx(2, 3 * math.pi / 8).Rx(1, 3 * math.pi / 8).Rx(0, 3 * math.pi / 8).Rx(3, 3 * math.pi / 8)
    circuit = circuit_builder.to_circuit()
    circuit.merge(SingleQubitGatesMerger())
    circuit.decompose(XYXDecomposer())
    assert np.allclose(circuit.phase_record.qubit_phase_record, [math.pi / 2, math.pi / 2, -math.pi / 2, math.pi / 2])
