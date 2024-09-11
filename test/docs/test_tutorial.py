import math

import numpy as np
import pytest

from opensquirrel import Circuit, CircuitBuilder
from opensquirrel.decomposer.aba_decomposer import ZYZDecomposer
from opensquirrel.default_gates import CNOT, CZ, H, Ry, Rz
from opensquirrel.ir import BlochSphereRotation, ControlledGate, Float, MatrixGate, Qubit, named_gate


def test_circuit_from_string() -> None:
    qc = Circuit.from_string(
        """
        version 3.0

        // Initialise a circuit with two qubits and a bit
        qubit[2] q
        bit[2] b

        // Create a Bell pair
        H q[0]
        CNOT q[0], q[1]

        // Measure qubits
        b = measure q
        """
    )

    assert (
        str(qc)
        == """version 3.0

qubit[2] q
bit[2] b

H q[0]
CNOT q[0], q[1]
b[0] = measure q[0]
b[1] = measure q[1]
"""
    )


def test_circuit_builder() -> None:
    builder = CircuitBuilder(qubit_register_size=2)
    builder.Ry(Qubit(0), Float(0.23)).CNOT(Qubit(0), Qubit(1))
    qc = builder.to_circuit()

    assert (
        str(qc)
        == """version 3.0

qubit[2] q

Ry(0.23) q[0]
CNOT q[0], q[1]
"""
    )


def test_circuit_builder_loop() -> None:
    builder = CircuitBuilder(qubit_register_size=10)
    for i in range(0, 10, 2):
        builder.H(Qubit(i))
    qc = builder.to_circuit()

    assert (
        str(qc)
        == """version 3.0

qubit[10] q

H q[0]
H q[2]
H q[4]
H q[6]
H q[8]
"""
    )


def test_circuit_builder_QFT() -> None:
    qubit_register_size = 5
    builder = CircuitBuilder(qubit_register_size)
    for i in range(qubit_register_size):
        builder.H(Qubit(i))
        for c in range(i + 1, qubit_register_size):
            builder.CRk(Qubit(c), Qubit(i), c - i + 1)
    qft = builder.to_circuit()

    assert (
        str(qft)
        == """version 3.0

qubit[5] q

H q[0]
CRk(2) q[1], q[0]
CRk(3) q[2], q[0]
CRk(4) q[3], q[0]
CRk(5) q[4], q[0]
H q[1]
CRk(2) q[2], q[1]
CRk(3) q[3], q[1]
CRk(4) q[4], q[1]
H q[2]
CRk(2) q[3], q[2]
CRk(3) q[4], q[2]
H q[3]
CRk(2) q[4], q[3]
H q[4]
"""
    )


def test_CNOT_strong_type_error_string() -> None:
    with pytest.raises(OSError, match=r".* with argument pack .*") as e_info:
        Circuit.from_string(
            """
            version 3.0
            qubit[2] q

            CNOT q[0], 3 // The CNOT expects a qubit as second argument.
            """
        )

    assert "failed to resolve instruction 'CNOT' with argument pack (qubit, int)" in str(e_info.value)


def test_CNOT_strong_type_error_builder() -> None:
    with pytest.raises(TypeError) as e_info:
        CircuitBuilder(qubit_register_size=2).CNOT(Qubit(0), 3)

    assert "wrong argument type for instruction `CNOT`, got <class 'int'> but expected Qubit" in str(e_info.value)


def test_anonymous_gate() -> None:
    builder = CircuitBuilder(1)
    for _ in range(4):
        builder.Rx(Qubit(0), Float(math.pi / 4))
    qc = builder.to_circuit()

    qc.merge_single_qubit_gates()

    assert (
        str(qc)
        == """version 3.0

qubit[1] q

Anonymous gate: BlochSphereRotation(Qubit[0], axis=[1. 0. 0.], angle=3.14159, phase=0.0)
"""
    )


def test_create_custom_gates() -> None:
    @named_gate
    def x(q: Qubit) -> BlochSphereRotation:
        return BlochSphereRotation(qubit=q, axis=(1, 0, 0), angle=math.pi, phase=math.pi / 2)

    @named_gate
    def cnot(control: Qubit, target: Qubit) -> ControlledGate:
        return ControlledGate(control, x(target))

    @named_gate
    def swap(q1: Qubit, q2: Qubit) -> MatrixGate:
        return MatrixGate(
            np.array(
                [
                    [1, 0, 0, 0],
                    [0, 0, 1, 0],
                    [0, 1, 0, 0],
                    [0, 0, 0, 1],
                ]
            ),
            [q1, q2],
        )

    assert x(Qubit(0)) == BlochSphereRotation(Qubit(0), axis=(1, 0, 0), angle=math.pi, phase=math.pi / 2)
    assert cnot(Qubit(0), Qubit(1)) == ControlledGate(Qubit(0), x(Qubit(1)))
    assert swap(Qubit(0), Qubit(1)) == MatrixGate(
        np.array(
            [
                [1, 0, 0, 0],
                [0, 0, 1, 0],
                [0, 1, 0, 0],
                [0, 0, 0, 1],
            ]
        ),
        [Qubit(0), Qubit(1)],
    )


def test_predefined_decomposition() -> None:
    qc = Circuit.from_string(
        """
        version 3.0
        qubit[3] q

        X q[0:2]  // Note that this notation is expanded in OpenSquirrel.
        CNOT q[0], q[1]
        Ry q[2], 6.78
        """
    )
    qc.replace(
        CNOT,
        lambda control, target: [
            H(target),
            CZ(control, target),
            H(target),
        ],
    )

    assert (
        str(qc)
        == """version 3.0

qubit[3] q

X q[0]
X q[1]
X q[2]
H q[1]
CZ q[0], q[1]
H q[1]
Ry(6.78) q[2]
"""
    )


def test_error_predefined_decomposition() -> None:
    qc = Circuit.from_string(
        """
        version 3.0
        qubit[3] q

        X q[0:2]
        CNOT q[0], q[1]
        Ry q[2], 6.78
        """
    )
    with pytest.raises(ValueError, match=r"replacement for gate .*") as e_info:
        qc.replace(
            CNOT,
            lambda control, target: [
                H(target),
                CZ(control, target),
            ],
        )

    assert str(e_info.value) == "replacement for gate CNOT does not preserve the quantum state"


def test_zyz_decomposer() -> None:
    builder = CircuitBuilder(qubit_register_size=1)
    builder.H(Qubit(0)).Z(Qubit(0)).Y(Qubit(0)).Rx(Qubit(0), Float(math.pi / 3))
    qc = builder.to_circuit()

    qc.decompose(decomposer=ZYZDecomposer())

    assert (
        str(qc)
        == """version 3.0

qubit[1] q

Rz(3.1415927) q[0]
Ry(1.5707963) q[0]
Rz(3.1415927) q[0]
Ry(3.1415927) q[0]
Rz(1.5707963) q[0]
Ry(1.0471976) q[0]
Rz(-1.5707963) q[0]
"""
    )

    assert ZYZDecomposer().decompose(H(Qubit(0))) == [Rz(Qubit(0), Float(math.pi)), Ry(Qubit(0), Float(math.pi / 2))]
