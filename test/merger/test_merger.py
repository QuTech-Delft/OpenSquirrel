import math
from test.ir_equality_test_base import modify_circuit_and_check

from opensquirrel.circuit import Circuit
from opensquirrel.default_gates import CNOT, H, Rx, Ry, Rz
from opensquirrel.ir import IR, BlochSphereRotation, Float, Qubit
from opensquirrel.merger import general_merger
from opensquirrel.merger.general_merger import compose_bloch_sphere_rotations
from opensquirrel.register_manager import RegisterManager


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
    register_manager = RegisterManager(qubit_register_size=2)
    ir = IR()
    ir.add_gate(Ry(Qubit(0), Float(1.2345)))
    circuit = Circuit(register_manager, ir)

    expected_ir = IR()
    expected_ir.add_gate(Ry(Qubit(0), Float(1.2345)))
    expected_circuit = Circuit(register_manager, expected_ir)

    modify_circuit_and_check(circuit, general_merger.merge_single_qubit_gates, expected_circuit)

    # Check that when no fusion happens, generator and arguments of gates are preserved.
    assert ir.statements[0].generator == Ry
    assert ir.statements[0].arguments == (Qubit(0), Float(1.2345))


def test_two_hadamards() -> None:
    register_manager = RegisterManager(qubit_register_size=4)
    ir = IR()
    ir.add_gate(H(Qubit(2)))
    ir.add_gate(H(Qubit(2)))
    circuit = Circuit(register_manager, ir)

    expected_ir = IR()
    expected_circuit = Circuit(register_manager, expected_ir)

    modify_circuit_and_check(circuit, general_merger.merge_single_qubit_gates, expected_circuit)


def test_two_hadamards_different_qubits() -> None:
    register_manager = RegisterManager(qubit_register_size=4)
    ir = IR()
    ir.add_gate(H(Qubit(0)))
    ir.add_gate(H(Qubit(2)))
    circuit = Circuit(register_manager, ir)

    expected_ir = IR()
    expected_ir.add_gate(H(Qubit(0)))
    expected_ir.add_gate(H(Qubit(2)))
    expected_circuit = Circuit(register_manager, expected_ir)

    modify_circuit_and_check(circuit, general_merger.merge_single_qubit_gates, expected_circuit)


def test_merge_different_qubits() -> None:
    register_manager = RegisterManager(qubit_register_size=4)
    ir = IR()
    ir.add_gate(Ry(Qubit(0), Float(math.pi / 2)))
    ir.add_gate(Rx(Qubit(0), Float(math.pi)))
    ir.add_gate(Rz(Qubit(1), Float(1.2345)))
    ir.add_gate(Ry(Qubit(2), Float(1)))
    ir.add_gate(Ry(Qubit(2), Float(3.234)))
    circuit = Circuit(register_manager, ir)

    expected_ir = IR()
    expected_ir.add_gate(
        BlochSphereRotation(qubit=Qubit(0), axis=(1, 0, 1), angle=math.pi)
    )  # This is hadamard with 0 phase...
    expected_ir.add_gate(Rz(Qubit(1), Float(1.2345)))
    expected_ir.add_gate(Ry(Qubit(2), Float(4.234)))
    expected_circuit = Circuit(register_manager, expected_ir)

    modify_circuit_and_check(circuit, general_merger.merge_single_qubit_gates, expected_circuit)

    assert ir.statements[0].is_anonymous  # When fusion happens, the resulting gate is anonymous.
    assert ir.statements[1].generator == Rz  # Otherwise it keeps the same generator and arguments.
    assert ir.statements[1].arguments == (Qubit(1), Float(1.2345))
    assert ir.statements[2].is_anonymous


def test_merge_and_flush() -> None:
    register_manager = RegisterManager(qubit_register_size=4)
    ir = IR()
    ir.add_gate(Ry(Qubit(0), Float(math.pi / 2)))
    ir.add_gate(Rz(Qubit(1), Float(1.5)))
    ir.add_gate(Rx(Qubit(0), Float(math.pi)))
    ir.add_gate(Rz(Qubit(1), Float(-2.5)))
    ir.add_gate(CNOT(Qubit(0), Qubit(1)))
    ir.add_gate(Ry(Qubit(0), Float(3.234)))
    circuit = Circuit(register_manager, ir)

    expected_ir = IR()
    expected_ir.add_gate(
        BlochSphereRotation(qubit=Qubit(0), axis=(1, 0, 1), angle=math.pi)
    )  # This is hadamard with 0 phase...
    expected_ir.add_gate(Rz(Qubit(1), Float(-1.0)))
    expected_ir.add_gate(CNOT(Qubit(0), Qubit(1)))
    expected_ir.add_gate(Ry(Qubit(0), Float(3.234)))
    expected_circuit = Circuit(register_manager, expected_ir)

    modify_circuit_and_check(circuit, general_merger.merge_single_qubit_gates, expected_circuit)

    assert ir.statements[0].is_anonymous
    assert ir.statements[3].generator == Ry
    assert ir.statements[3].arguments, (Qubit(0), Float(3.234))
