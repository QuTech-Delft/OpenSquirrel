import numpy as np

from opensquirrel import CircuitBuilder
from opensquirrel.ir import BlochSphereRotation, ControlledGate, Float, MatrixGate, Qubit
from opensquirrel.writer import writer


def test_write() -> None:
    builder = CircuitBuilder(3)
    circuit = builder.to_circuit()

    assert (
        writer.circuit_to_string(circuit)
        == """version 3.0

qubit[3] q

"""
    )

    builder.H(Qubit(0))
    builder.CR(Qubit(0), Qubit(1), Float(1.234))
    circuit = builder.to_circuit()

    assert (
        writer.circuit_to_string(circuit)
        == """version 3.0

qubit[3] q

H q[0]
CR(1.234) q[0], q[1]
"""
    )


def test_anonymous_gate() -> None:
    builder = CircuitBuilder(2, 2)
    builder.H(Qubit(0))
    builder.ir.add_gate(BlochSphereRotation(Qubit(0), axis=(1, 1, 1), angle=1.23))
    builder.ir.add_gate(ControlledGate(Qubit(0), BlochSphereRotation(Qubit(0), axis=(1, 1, 1), angle=1.23)))
    builder.ir.add_gate(
        MatrixGate(np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]]), [Qubit(0), Qubit(1)])
    )
    builder.CR(Qubit(0), Qubit(1), Float(1.234))
    assert (
        str(builder.to_circuit())
        == """version 3.0

qubit[2] q
bit[2] b

H q[0]
Anonymous gate: BlochSphereRotation(Qubit[0], axis=[0.57735 0.57735 0.57735], angle=1.23, phase=0.0)
Anonymous gate: ControlledGate(control_qubit=Qubit[0], BlochSphereRotation(Qubit[0], axis=[0.57735 0.57735 0.57735], angle=1.23, phase=0.0))
Anonymous gate: MatrixGate(qubits=[Qubit[0], Qubit[1]], matrix=[[1 0 0 0] [0 1 0 0] [0 0 0 1] [0 0 1 0]])
CR(1.234) q[0], q[1]
"""
    )


def test_comment() -> None:
    builder = CircuitBuilder(3)
    builder.H(Qubit(0))
    builder.comment("My comment")
    builder.CR(Qubit(0), Qubit(1), Float(1.234))
    circuit = builder.to_circuit()
    assert (
        writer.circuit_to_string(circuit)
        == """version 3.0

qubit[3] q

H q[0]

/* My comment */

CR(1.234) q[0], q[1]
"""
    )


def test_cap_significant_digits() -> None:
    builder = CircuitBuilder(3)
    builder.CR(Qubit(0), Qubit(1), Float(1.6546514861321684321654))
    circuit = builder.to_circuit()

    assert (
        writer.circuit_to_string(circuit)
        == """version 3.0

qubit[3] q

CR(1.6546515) q[0], q[1]
"""
    )
