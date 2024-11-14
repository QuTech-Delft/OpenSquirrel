import math

import pytest

from opensquirrel import Circuit, CircuitBuilder
from opensquirrel.default_gates import Ry, Rz
from opensquirrel.ir import Bit, BlochSphereRotation, Float, Qubit
from opensquirrel.merger import general_merger
from opensquirrel.merger.general_merger import compose_bloch_sphere_rotations
from test.ir_equality_test_base import modify_circuit_and_check


def test_compose_bloch_sphere_rotations_same_axis() -> None:
    a = BlochSphereRotation(qubit=123, axis=(1, 2, 3), angle=0.4)
    b = BlochSphereRotation(qubit=123, axis=(1, 2, 3), angle=-0.3)
    composed = compose_bloch_sphere_rotations(a, b)
    assert composed == BlochSphereRotation(qubit=123, axis=(1, 2, 3), angle=0.1)


def test_compose_bloch_sphere_rotations_different_axis() -> None:
    # Visualizing this in 3D is difficult...
    a = BlochSphereRotation(qubit=123, axis=(1, 0, 0), angle=math.pi / 2)
    b = BlochSphereRotation(qubit=123, axis=(0, 0, 1), angle=-math.pi / 2)
    c = BlochSphereRotation(qubit=123, axis=(0, 1, 0), angle=math.pi / 2)
    composed = compose_bloch_sphere_rotations(a, compose_bloch_sphere_rotations(b, c))
    assert composed == BlochSphereRotation(qubit=123, axis=(1, 1, 0), angle=math.pi)


def test_single_gate() -> None:
    builder1 = CircuitBuilder(1)
    builder1.Ry(0, Float(1.2345))
    circuit = builder1.to_circuit()

    builder2 = CircuitBuilder(1)
    builder2.Ry(0, Float(1.2345))
    expected_circuit = builder2.to_circuit()

    modify_circuit_and_check(circuit, general_merger.merge_single_qubit_gates, expected_circuit)

    # Check that when no fusion happens, generator and arguments of gates are preserved.
    assert isinstance(circuit.ir.statements[0], BlochSphereRotation)
    assert circuit.ir.statements[0].generator == Ry
    assert circuit.ir.statements[0].arguments == (Qubit(0), Float(1.2345))


def test_two_hadamards() -> None:
    builder = CircuitBuilder(4)
    builder.H(2)
    builder.H(2)
    circuit = builder.to_circuit()

    expected_circuit = CircuitBuilder(4).to_circuit()

    modify_circuit_and_check(circuit, general_merger.merge_single_qubit_gates, expected_circuit)


def test_two_hadamards_different_qubits() -> None:
    builder1 = CircuitBuilder(4)
    builder1.H(0)
    builder1.H(2)
    circuit = builder1.to_circuit()

    builder2 = CircuitBuilder(4)
    builder2.H(0)
    builder2.H(2)
    expected_circuit = builder2.to_circuit()

    modify_circuit_and_check(circuit, general_merger.merge_single_qubit_gates, expected_circuit)


def test_merge_different_qubits() -> None:
    builder1 = CircuitBuilder(4)
    builder1.Ry(0, Float(math.pi / 2))
    builder1.Rx(0, Float(math.pi))
    builder1.Rz(1, Float(1.2345))
    builder1.Ry(2, Float(1))
    builder1.Ry(2, Float(3.234))
    circuit = builder1.to_circuit()

    builder2 = CircuitBuilder(4)
    builder2.ir.add_gate(BlochSphereRotation(0, axis=(1, 0, 1), angle=math.pi))  # this is Hadamard with 0 phase
    builder2.Rz(1, Float(1.2345))
    builder2.Ry(2, Float(4.234))
    expected_circuit = builder2.to_circuit()

    modify_circuit_and_check(circuit, general_merger.merge_single_qubit_gates, expected_circuit)

    assert isinstance(circuit.ir.statements[0], BlochSphereRotation)
    assert circuit.ir.statements[0].is_anonymous  # When fusion happens, the resulting gate is anonymous.

    assert isinstance(circuit.ir.statements[1], BlochSphereRotation)
    assert circuit.ir.statements[1].generator == Rz  # Otherwise it keeps the same generator and arguments.
    assert circuit.ir.statements[1].arguments == (Qubit(1), Float(1.2345))

    assert isinstance(circuit.ir.statements[2], BlochSphereRotation)
    assert circuit.ir.statements[2].is_anonymous


def test_merge_and_flush() -> None:
    builder1 = CircuitBuilder(4)
    builder1.Ry(0, Float(math.pi / 2))
    builder1.Rz(1, Float(1.5))
    builder1.Rx(0, Float(math.pi))
    builder1.Rz(1, Float(-2.5))
    builder1.CNOT(0, 1)
    builder1.Ry(0, Float(3.234))
    circuit = builder1.to_circuit()

    builder2 = CircuitBuilder(4)
    builder2.ir.add_gate(BlochSphereRotation(0, axis=(1, 0, 1), angle=math.pi))  # this is Hadamard with 0 phase
    builder2.Rz(1, Float(-1.0))
    builder2.CNOT(0, 1)
    builder2.Ry(0, Float(3.234))
    expected_circuit = builder2.to_circuit()

    modify_circuit_and_check(circuit, general_merger.merge_single_qubit_gates, expected_circuit)

    assert isinstance(circuit.ir.statements[0], BlochSphereRotation)
    assert circuit.ir.statements[0].is_anonymous

    assert isinstance(circuit.ir.statements[3], BlochSphereRotation)
    assert circuit.ir.statements[3].generator == Ry
    assert circuit.ir.statements[3].arguments == (Qubit(0), Float(3.234))


def test_merge_y90_x_to_h() -> None:
    builder = CircuitBuilder(1)
    builder.Y90(0)
    builder.X(0)
    qc = builder.to_circuit()

    builder2 = CircuitBuilder(1)
    builder2.H(0)
    expected_qc = builder2.to_circuit()
    modify_circuit_and_check(qc, general_merger.merge_single_qubit_gates, expected_qc)


def test_no_merge_across_measure() -> None:
    builder = CircuitBuilder(2, 2)
    builder.H(0)
    builder.measure(0, Bit(0))
    builder.H(0)
    builder.H(1)
    builder.measure(0, Bit(1))
    builder.H(1)
    qc = builder.to_circuit()

    builder2 = CircuitBuilder(2, 2)
    builder2.H(0)
    builder2.measure(0, Bit(0))
    builder2.H(0)
    builder2.measure(0, Bit(1))
    expected_qc = builder2.to_circuit()
    modify_circuit_and_check(qc, general_merger.merge_single_qubit_gates, expected_qc)


def test_no_merge_across_reset() -> None:
    builder = CircuitBuilder(2)
    builder.H(0)
    builder.reset(0)
    builder.H(0)
    builder.H(1)
    builder.reset(0)
    builder.H(1)
    qc = builder.to_circuit()

    builder2 = CircuitBuilder(2)
    builder2.H(0)
    builder2.reset(0)
    builder2.H(0)
    builder2.reset(0)
    expected_qc = builder2.to_circuit()
    modify_circuit_and_check(qc, general_merger.merge_single_qubit_gates, expected_qc)


@pytest.mark.parametrize(
    ("circuit", "expected_result"),
    [
        (
            CircuitBuilder(2).H(0).barrier(0).H(1).barrier(1).H(0).Rx(0, Float(math.pi / 3)).barrier(0).to_circuit(),
            """version 3.0

qubit[2] q

H q[0]
H q[1]
barrier q[0]
H q[0]
Rx(1.0471976) q[0]
barrier q[1]
barrier q[0]
""",
        ),
        (
            CircuitBuilder(2).X(0).barrier(0).X(1).barrier(1).CNOT(0, 1).barrier(1).X(1).to_circuit(),
            """version 3.0

qubit[2] q

X q[0]
X q[1]
barrier q[0]
barrier q[1]
CNOT q[0], q[1]
barrier q[1]
X q[1]
""",
        ),
        (
            CircuitBuilder(2).X(0).X(1).barrier(0).barrier(1).X(0).to_circuit(),
            """version 3.0

qubit[2] q

X q[0]
X q[1]
barrier q[0]
barrier q[1]
X q[0]
""",
        ),
        (
            CircuitBuilder(4)
            .H(0)
            .barrier(0)
            .H(1)
            .barrier(1)
            .H(2)
            .barrier(2)
            .H(3)
            .barrier(3)
            .CNOT(0, 3)
            .barrier(0)
            .barrier(1)
            .barrier(3)
            .to_circuit(),
            """version 3.0

qubit[4] q

H q[0]
H q[1]
H q[2]
H q[3]
barrier q[0]
barrier q[1]
barrier q[2]
barrier q[3]
CNOT q[0], q[3]
barrier q[0]
barrier q[1]
barrier q[3]
""",
        ),
    ],
    ids=[
        "anonymous_gate",
        "CNOT_cannot_go_through_a_group_of_linked_barriers",
        "X_cannot_go_through_a_group_of_linked_barriers",
        "circuit_with_4_qubits",
    ],
)
def test_rearrange_barriers(circuit: Circuit, expected_result: str) -> None:
    from opensquirrel.merger.general_merger import rearrange_barriers

    rearrange_barriers(circuit.ir)
    assert str(circuit) == expected_result


@pytest.mark.parametrize(
    ("circuit", "expected_result"),
    [
        (
            (
                CircuitBuilder(2)
                .H(1)
                .Rz(1, Float(2.332))
                .H(0)
                .Rx(0, Float(1.423))
                .barrier(0)
                .barrier(1)
                .H(1)
                .Rz(1, Float(2.332))
                .H(0)
                .Rx(1, Float(1.423))
                .barrier(0)
                .barrier(1)
                .to_circuit()
            ),
            """version 3.0

qubit[2] q

Anonymous gate: BlochSphereRotation(Qubit[0], axis=[ 0.60376 -0.52053  0.60376], angle=-2.18173, phase=1.5708)
Anonymous gate: BlochSphereRotation(Qubit[1], axis=[0.36644 0.85525 0.36644], angle=-1.72653, phase=1.5708)
barrier q[0]
barrier q[1]
H q[0]
Anonymous gate: BlochSphereRotation(Qubit[1], axis=[ 0.28903 -0.42028 -0.86013], angle=1.66208, phase=1.5708)
barrier q[0]
barrier q[1]
""",
        ),
        (
            CircuitBuilder(3)
            .H(0)
            .Ry(0, Float(2))
            .barrier(2)
            .barrier(0)
            .barrier(1)
            .H(0)
            .H(1)
            .Ry(1, Float(2))
            .barrier(1)
            .H(2)
            .barrier(2)
            .barrier(0)
            .barrier(1)
            .to_circuit(),
            """version 3.0

qubit[3] q

Anonymous gate: BlochSphereRotation(Qubit[0], axis=[ 0.97706  0.      -0.21296], angle=3.14159, phase=1.5708)
barrier q[2]
barrier q[0]
barrier q[1]
H q[0]
Anonymous gate: BlochSphereRotation(Qubit[1], axis=[ 0.97706  0.      -0.21296], angle=3.14159, phase=1.5708)
H q[2]
barrier q[1]
barrier q[2]
barrier q[0]
barrier q[1]
""",
        ),
        (
            CircuitBuilder(2)
            .H(0)
            .Ry(0, Float(2))
            .barrier(1)
            .barrier(0)
            .barrier(1)
            .H(0)
            .H(1)
            .Ry(1, Float(2))
            .barrier(1)
            .to_circuit(),
            """version 3.0

qubit[2] q

Anonymous gate: BlochSphereRotation(Qubit[0], axis=[ 0.97706  0.      -0.21296], angle=3.14159, phase=1.5708)
barrier q[1]
barrier q[0]
barrier q[1]
H q[0]
Anonymous gate: BlochSphereRotation(Qubit[1], axis=[ 0.97706  0.      -0.21296], angle=3.14159, phase=1.5708)
barrier q[1]
""",
        ),
    ],
    ids=["generic_case", "circuit_with_irregular_barrier_order", "repeating_barrier"],
)
def test_sticky_barriers(circuit: Circuit, expected_result: str) -> None:
    circuit.merge_single_qubit_gates()
    from opensquirrel.merger.general_merger import rearrange_barriers

    rearrange_barriers(circuit.ir)
    assert str(circuit) == expected_result
