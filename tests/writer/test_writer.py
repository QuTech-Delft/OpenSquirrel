from opensquirrel import CircuitBuilder
from opensquirrel.ir import BlochSphereRotation, ControlledGate, MatrixGate
from opensquirrel.writer import writer


def test_circuit_without_bits() -> None:
    builder = CircuitBuilder(3)
    circuit = builder.to_circuit()
    assert (
        writer.circuit_to_string(circuit)
        == """version 3.0

qubit[3] q
"""
    )


def test_circuit_with_qubits_and_bits() -> None:
    builder = CircuitBuilder(3, 3)
    circuit = builder.to_circuit()
    assert (
        writer.circuit_to_string(circuit)
        == """version 3.0

qubit[3] q
bit[3] b
"""
    )


def test_circuit_to_string_after_circuit_modification() -> None:
    builder = CircuitBuilder(3)
    circuit = builder.to_circuit()
    assert (
        writer.circuit_to_string(circuit)
        == """version 3.0

qubit[3] q
"""
    )

    builder.H(0)
    builder.CR(0, 1, 1.234)
    circuit = builder.to_circuit()
    assert (
        writer.circuit_to_string(circuit)
        == """version 3.0

qubit[3] q

H q[0]
CR(1.234) q[0], q[1]
"""
    )


def test_float_precision() -> None:
    builder = CircuitBuilder(3)
    builder.CR(0, 1, 1.6546514861321684321654)
    circuit = builder.to_circuit()
    assert (
        writer.circuit_to_string(circuit)
        == """version 3.0

qubit[3] q

CR(1.6546515) q[0], q[1]
"""
    )


def test_measure() -> None:
    builder = CircuitBuilder(1, 1)
    builder.H(0)
    builder.measure(0, 0)
    circuit = builder.to_circuit()
    assert (
        writer.circuit_to_string(circuit)
        == """version 3.0

qubit[1] q
bit[1] b

H q[0]
b[0] = measure q[0]
"""
    )


def test_swap() -> None:
    builder = CircuitBuilder(2, 2)
    builder.SWAP(0, 1)
    circuit = builder.to_circuit()
    assert (
        writer.circuit_to_string(circuit)
        == """version 3.0

qubit[2] q
bit[2] b

SWAP q[0], q[1]
"""
    )


def test_anonymous_gate() -> None:
    builder = CircuitBuilder(2, 2)
    builder.H(0)
    builder.ir.add_gate(BlochSphereRotation(0, axis=(1, 1, 1), angle=1.23, phase=0.0))
    builder.ir.add_gate(ControlledGate(0, BlochSphereRotation(1, axis=(1, 1, 1), angle=1.23, phase=0.0)))
    builder.ir.add_gate(MatrixGate([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]], [0, 1]))
    builder.CR(0, 1, 1.234)
    assert (
        str(builder.to_circuit())
        == """version 3.0

qubit[2] q
bit[2] b

H q[0]
BlochSphereRotation(qubit=Qubit[0], axis=[0.57735 0.57735 0.57735], angle=1.23, phase=0.0)
ControlledGate(control_qubit=Qubit[0], target_gate=BlochSphereRotation(qubit=Qubit[1], axis=[0.57735 0.57735 0.57735], angle=1.23, phase=0.0))
MatrixGate(qubits=[Qubit[0], Qubit[1]], matrix=[[1.+0.j 0.+0.j 0.+0.j 0.+0.j] [0.+0.j 1.+0.j 0.+0.j 0.+0.j] [0.+0.j 0.+0.j 0.+0.j 1.+0.j] [0.+0.j 0.+0.j 1.+0.j 0.+0.j]])
CR(1.234) q[0], q[1]
"""  # noqa: E501
    )
