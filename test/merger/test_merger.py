import unittest
from test.ir_equality_test_base import IREqualityTestBase

from open_squirrel.circuit import Circuit
from open_squirrel.default_gates import *
from open_squirrel.merger import general_merger
from open_squirrel.merger.general_merger import compose_bloch_sphere_rotations
from open_squirrel.register_manager import RegisterManager
from open_squirrel.ir import Float, Qubit, IR


class MergerTest(IREqualityTestBase):
    def test_compose_bloch_sphere_rotations_same_axis(self):
        q = Qubit(123)
        a = BlochSphereRotation(qubit=q, axis=(1, 2, 3), angle=0.4)
        b = BlochSphereRotation(qubit=q, axis=(1, 2, 3), angle=-0.3)
        composed = compose_bloch_sphere_rotations(a, b)
        self.assertEqual(composed, BlochSphereRotation(qubit=q, axis=(1, 2, 3), angle=0.1))

    def test_compose_bloch_sphere_rotations_different_axis(self):
        # Visualizing this in 3D is difficult...
        q = Qubit(123)
        a = BlochSphereRotation(qubit=q, axis=(1, 0, 0), angle=math.pi / 2)
        b = BlochSphereRotation(qubit=q, axis=(0, 0, 1), angle=-math.pi / 2)
        c = BlochSphereRotation(qubit=q, axis=(0, 1, 0), angle=math.pi / 2)
        composed = compose_bloch_sphere_rotations(a, compose_bloch_sphere_rotations(b, c))
        self.assertEqual(composed, BlochSphereRotation(qubit=q, axis=(1, 1, 0), angle=math.pi))

    def test_single_gate(self):
        register_manager = RegisterManager(qubit_register_size=2)
        ir = IR()
        ir.add_gate(Ry(Qubit(0), Float(1.2345)))
        circuit = Circuit(register_manager, ir)

        expected_ir = IR()
        expected_ir.add_gate(Ry(Qubit(0), Float(1.2345)))
        expected_circuit = Circuit(register_manager, expected_ir)

        self.modify_circuit_and_check(circuit, general_merger.merge_single_qubit_gates, expected_circuit)

        # Check that when no fusion happens, generator and arguments of gates are preserved.
        self.assertEqual(ir.statements[0].generator, Ry)
        self.assertEqual(ir.statements[0].arguments, (Qubit(0), Float(1.2345)))

    def test_two_hadamards(self):
        register_manager = RegisterManager(qubit_register_size=4)
        ir = IR()
        ir.add_gate(H(Qubit(2)))
        ir.add_gate(H(Qubit(2)))
        circuit = Circuit(register_manager, ir)

        expected_ir = IR()
        expected_circuit = Circuit(register_manager, expected_ir)

        self.modify_circuit_and_check(circuit, general_merger.merge_single_qubit_gates, expected_circuit)

    def test_two_hadamards_different_qubits(self):
        register_manager = RegisterManager(qubit_register_size=4)
        ir = IR()
        ir.add_gate(H(Qubit(0)))
        ir.add_gate(H(Qubit(2)))
        circuit = Circuit(register_manager, ir)

        expected_ir = IR()
        expected_ir.add_gate(H(Qubit(0)))
        expected_ir.add_gate(H(Qubit(2)))
        expected_circuit = Circuit(register_manager, expected_ir)

        self.modify_circuit_and_check(circuit, general_merger.merge_single_qubit_gates, expected_circuit)

    def test_merge_different_qubits(self):
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

        self.modify_circuit_and_check(circuit, general_merger.merge_single_qubit_gates, expected_circuit)

        self.assertTrue(ir.statements[0].is_anonymous)  # When fusion happens, the resulting gate is anonymous.
        self.assertEqual(ir.statements[1].generator, Rz)  # Otherwise it keeps the same generator and arguments.
        self.assertEqual(ir.statements[1].arguments, (Qubit(1), Float(1.2345)))
        self.assertTrue(ir.statements[2].is_anonymous)

    def test_merge_and_flush(self):
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

        self.modify_circuit_and_check(circuit, general_merger.merge_single_qubit_gates, expected_circuit)

        self.assertTrue(ir.statements[0].is_anonymous)
        self.assertEqual(ir.statements[3].generator, Ry)
        self.assertEqual(ir.statements[3].arguments, (Qubit(0), Float(3.234)))


if __name__ == "__main__":
    unittest.main()
