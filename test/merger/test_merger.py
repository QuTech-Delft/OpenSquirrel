import math
from test.ir_equality_test_base import modify_circuit_and_check

from opensquirrel import CircuitBuilder
from opensquirrel.default_gates import Ry, Rz
from opensquirrel.ir import BlochSphereRotation, Float, Qubit
from opensquirrel.merger import general_merger
from opensquirrel.merger.general_merger import compose_bloch_sphere_rotations


def test_compose_bloch_sphere_rotations_same_axis() -> None:
    q = Qubit(123)
    a = BlochSphereRotation(qubit=q, axis=(1, 2, 3), angle=0.4)
    b = BlochSphereRotation(qubit=q, axis=(1, 2, 3), angle=-0.3)
    composed = compose_bloch_sphere_rotations(a, b)
    assert composed == BlochSphereRotation(qubit=q, axis=(1, 2, 3), angle=0.1)


def test_compose_bloch_sphere_rotations_different_axis() -> None:
    # Visualizing this in 3D is difficult...
    q = Qubit(123)
    a = BlochSphereRotation(qubit=q, axis=(1, 0, 0), angle=math.pi / 2)
    b = BlochSphereRotation(qubit=q, axis=(0, 0, 1), angle=-math.pi / 2)
    c = BlochSphereRotation(qubit=q, axis=(0, 1, 0), angle=math.pi / 2)
    composed = compose_bloch_sphere_rotations(a, compose_bloch_sphere_rotations(b, c))
    assert composed == BlochSphereRotation(qubit=q, axis=(1, 1, 0), angle=math.pi)


def test_single_gate() -> None:
    builder1 = CircuitBuilder(1)
    builder1.Ry(Qubit(0), Float(1.2345))
    circuit = builder1.to_circuit()

    builder2 = CircuitBuilder(1)
    builder2.Ry(Qubit(0), Float(1.2345))
    expected_circuit = builder2.to_circuit()

    modify_circuit_and_check(circuit, general_merger.merge_single_qubit_gates, expected_circuit)

    # Check that when no fusion happens, generator and arguments of gates are preserved.
    assert isinstance(circuit.ir.statements[0], BlochSphereRotation)
    assert circuit.ir.statements[0].generator == Ry
    assert circuit.ir.statements[0].arguments == (Qubit(0), Float(1.2345))


def test_two_hadamards() -> None:
    builder = CircuitBuilder(4)
    builder.H(Qubit(2))
    builder.H(Qubit(2))
    circuit = builder.to_circuit()

    expected_circuit = CircuitBuilder(4).to_circuit()

    modify_circuit_and_check(circuit, general_merger.merge_single_qubit_gates, expected_circuit)


def test_two_hadamards_different_qubits() -> None:
    builder1 = CircuitBuilder(4)
    builder1.H(Qubit(0))
    builder1.H(Qubit(2))
    circuit = builder1.to_circuit()

    builder2 = CircuitBuilder(4)
    builder2.H(Qubit(0))
    builder2.H(Qubit(2))
    expected_circuit = builder2.to_circuit()

    modify_circuit_and_check(circuit, general_merger.merge_single_qubit_gates, expected_circuit)


def test_merge_different_qubits() -> None:
    builder1 = CircuitBuilder(4)
    builder1.Ry(Qubit(0), Float(math.pi / 2))
    builder1.Rx(Qubit(0), Float(math.pi))
    builder1.Rz(Qubit(1), Float(1.2345))
    builder1.Ry(Qubit(2), Float(1))
    builder1.Ry(Qubit(2), Float(3.234))
    circuit = builder1.to_circuit()

    builder2 = CircuitBuilder(4)
    builder2.ir.add_gate(BlochSphereRotation(Qubit(0), axis=(1, 0, 1), angle=math.pi))  # this is Hadamard with 0 phase
    builder2.Rz(Qubit(1), Float(1.2345))
    builder2.Ry(Qubit(2), Float(4.234))
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
    builder1.Ry(Qubit(0), Float(math.pi / 2))
    builder1.Rz(Qubit(1), Float(1.5))
    builder1.Rx(Qubit(0), Float(math.pi))
    builder1.Rz(Qubit(1), Float(-2.5))
    builder1.CNOT(Qubit(0), Qubit(1))
    builder1.Ry(Qubit(0), Float(3.234))
    circuit = builder1.to_circuit()

    builder2 = CircuitBuilder(4)
    builder2.ir.add_gate(BlochSphereRotation(Qubit(0), axis=(1, 0, 1), angle=math.pi))  # this is Hadamard with 0 phase
    builder2.Rz(Qubit(1), Float(-1.0))
    builder2.CNOT(Qubit(0), Qubit(1))
    builder2.Ry(Qubit(0), Float(3.234))
    expected_circuit = builder2.to_circuit()

    modify_circuit_and_check(circuit, general_merger.merge_single_qubit_gates, expected_circuit)

    assert isinstance(circuit.ir.statements[0], BlochSphereRotation)
    assert circuit.ir.statements[0].is_anonymous

    assert isinstance(circuit.ir.statements[3], BlochSphereRotation)
    assert circuit.ir.statements[3].generator == Ry
    assert circuit.ir.statements[3].arguments, (Qubit(0), Float(3.234))


def test_merge_y90_x_to_h() -> None:
    builder = CircuitBuilder(1)
    builder.Y90(Qubit(0))
    builder.X(Qubit(0))
    qc = builder.to_circuit()

    builder2 = CircuitBuilder(1)
    builder2.H(Qubit(0))
    expected_qc = builder2.to_circuit()
    modify_circuit_and_check(qc, general_merger.merge_single_qubit_gates, expected_qc)
