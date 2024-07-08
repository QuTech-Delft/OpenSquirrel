import math

from opensquirrel import CircuitBuilder
from opensquirrel.ir import Float, Qubit


def test_anonymous_gate():

    builder = CircuitBuilder(1)
    for i in range(4):
        builder.Rx(Qubit(0), Float(math.pi / 4))

    circuit = builder.to_circuit()

    circuit.merge_single_qubit_gates()

    assert (
        str(circuit)
        == """version 3.0

qubit[1] q

BlochSphereRotation(Qubit[0], axis=[1. 0. 0.], angle=3.14159, phase=0.0)
"""
    )
