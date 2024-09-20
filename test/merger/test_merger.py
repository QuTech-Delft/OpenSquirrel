import math

from opensquirrel import CircuitBuilder
from opensquirrel.default_gates import Ry, Rz
from opensquirrel.ir import Bit, BlochSphereRotation, Qubit, Float
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
    builder1.Ry(0, 1.2345)
    circuit = builder1.to_circuit()

    builder2 = CircuitBuilder(1)
    builder2.Ry(0, 1.2345)
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
    builder1.Ry(0, math.pi / 2)
    builder1.Rx(0, math.pi)
    builder1.Rz(1, 1.2345)
    builder1.Ry(2, 1)
    builder1.Ry(2, 3.234)
    circuit = builder1.to_circuit()

    builder2 = CircuitBuilder(4)
    builder2.ir.add_gate(BlochSphereRotation(0, axis=(1, 0, 1), angle=math.pi))  # this is Hadamard with 0 phase
    builder2.Rz(1, 1.2345)
    builder2.Ry(2, 4.234)
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
    builder1.Ry(0, math.pi / 2)
    builder1.Rz(1, 1.5)
    builder1.Rx(0, math.pi)
    builder1.Rz(1, -2.5)
    builder1.CNOT(0, 1)
    builder1.Ry(0, 3.234)
    circuit = builder1.to_circuit()

    builder2 = CircuitBuilder(4)
    builder2.ir.add_gate(BlochSphereRotation(0, axis=(1, 0, 1), angle=math.pi))  # this is Hadamard with 0 phase
    builder2.Rz(1, -1.0)
    builder2.CNOT(0, 1)
    builder2.Ry(0, 3.234)
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
