import math

import numpy as np
import pytest

from opensquirrel import CNOT, CZ, Circuit, CircuitBuilder, H, Ry, Rz
from opensquirrel.ir import BlochSphereRotation, ControlledGate, MatrixGate, QubitLike
from opensquirrel.passes.decomposer import ZYZDecomposer
from opensquirrel.passes.merger.single_qubit_gates_merger import SingleQubitGatesMerger


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
    builder.Ry(0, 0.23).CNOT(0, 1)
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
        builder.H(i)
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


def test_circuit_builder_qft() -> None:
    qubit_register_size = 5
    builder = CircuitBuilder(qubit_register_size)
    for i in range(qubit_register_size):
        builder.H(i)
        for c in range(i + 1, qubit_register_size):
            builder.CRk(c, i, c - i + 1)
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


def test_CNOT_strong_type_error_string() -> None:  # noqa: N802
    with pytest.raises(OSError, match=r".* with argument pack .*") as e_info:
        Circuit.from_string(
            """
            version 3.0
            qubit[2] q

            CNOT q[0], 3 // The CNOT expects a qubit as second argument.
            """
        )

    assert "failed to resolve instruction 'CNOT' with argument pack (qubit, int)" in str(e_info.value)


def test_anonymous_gate() -> None:
    builder = CircuitBuilder(1)
    for _ in range(4):
        builder.Rx(0, math.pi / 4)
    qc = builder.to_circuit()

    qc.merge(merger=SingleQubitGatesMerger())

    assert (
        str(qc)
        == """version 3.0

qubit[1] q

BlochSphereRotation(qubit=Qubit[0], axis=[1. 0. 0.], angle=3.14159, phase=0.0)
"""
    )


def test_create_custom_gates() -> None:
    class x(BlochSphereRotation):  # noqa: N801
        def __init__(self, qubit: QubitLike) -> None:
            BlochSphereRotation.__init__(self, qubit=qubit, axis=(1, 0, 0), angle=math.pi, phase=math.pi / 2, name="x")

    class cnot(ControlledGate):  # noqa: N801
        def __init__(self, control: QubitLike, target: QubitLike) -> None:
            ControlledGate.__init__(self, control_qubit=control, target_gate=x(target), name="cnot")

    class swap(MatrixGate):  # noqa: N801
        def __init__(self, qubit_0: QubitLike, qubit_1: QubitLike) -> None:
            MatrixGate.__init__(
                self,
                matrix=np.array(
                    [
                        [1, 0, 0, 0],
                        [0, 0, 1, 0],
                        [0, 1, 0, 0],
                        [0, 0, 0, 1],
                    ]
                ),
                operands=[qubit_0, qubit_1],
                name="swap",
            )

    assert x(0) == BlochSphereRotation(0, axis=(1, 0, 0), angle=math.pi, phase=math.pi / 2, name="x")
    assert cnot(0, 1) == ControlledGate(0, x(1), name="cnot")
    assert swap(0, 1) == MatrixGate(
        matrix=np.array(
            [
                [1, 0, 0, 0],
                [0, 0, 1, 0],
                [0, 1, 0, 0],
                [0, 0, 0, 1],
            ]
        ),
        operands=[0, 1],
        name="swap",
    )


def test_predefined_decomposition() -> None:
    qc = Circuit.from_string(
        """
        version 3.0
        qubit[3] q

        X q[0:2]  // Note that this notation is expanded in OpenSquirrel.
        CNOT q[0], q[1]
        Ry(6.78) q[2]
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
        Ry(6.78) q[2]
        """
    )
    with pytest.raises(ValueError, match=r"replacement for gate .*") as e_info:
        qc.replace(CNOT, lambda control_qubit, target_qubit: [H(target_qubit), CZ(control_qubit, target_qubit)])

    assert str(e_info.value) == "replacement for gate CNOT does not preserve the quantum state"


def test_zyz_decomposer() -> None:
    builder = CircuitBuilder(qubit_register_size=1)
    builder.H(0).Z(0).Y(0).Rx(0, math.pi / 3)
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

    assert ZYZDecomposer().decompose(H(0)) == [Rz(0, math.pi), Ry(0, math.pi / 2)]
