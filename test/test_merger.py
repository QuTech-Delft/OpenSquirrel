import unittest
from test.ir_equality_test_base import IREqualityTestBase

from opensquirrel.default_gates import *
from opensquirrel.merge import merger
from opensquirrel.merge.merger import compose_bloch_sphere_rotations
from opensquirrel.squirrel_ir import Float, Qubit, SquirrelIR


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
        ir = SquirrelIR(number_of_qubits=2, qubit_register_name="q")
        ir.add_gate(Ry(Qubit(0), Float(1.2345)))

        expected_ir = SquirrelIR(number_of_qubits=2, qubit_register_name="q")
        expected_ir.add_gate(Ry(Qubit(0), Float(1.2345)))

        self.modify_ir_and_check(ir, action=merger.merge_single_qubit_gates, expected_ir=expected_ir)

        # Check that when no fusion happens, generator and arguments of gates are preserved.
        self.assertEqual(ir.statements[0].generator, Ry)
        self.assertEqual(ir.statements[0].arguments, (Qubit(0), Float(1.2345)))

    def test_two_hadamards(self):
        ir = SquirrelIR(number_of_qubits=4, qubit_register_name="q")

        ir.add_gate(H(Qubit(2)))
        ir.add_gate(H(Qubit(2)))

        expected_ir = SquirrelIR(number_of_qubits=4, qubit_register_name="q")

        self.modify_ir_and_check(ir, action=merger.merge_single_qubit_gates, expected_ir=expected_ir)

    def test_two_hadamards_different_qubits(self):
        ir = SquirrelIR(number_of_qubits=4, qubit_register_name="q")
        ir.add_gate(H(Qubit(0)))
        ir.add_gate(H(Qubit(2)))

        expected_ir = SquirrelIR(number_of_qubits=4, qubit_register_name="q")
        expected_ir.add_gate(H(Qubit(0)))
        expected_ir.add_gate(H(Qubit(2)))

        self.modify_ir_and_check(ir, action=merger.merge_single_qubit_gates, expected_ir=expected_ir)

    def test_merge_different_qubits(self):
        ir = SquirrelIR(number_of_qubits=4, qubit_register_name="q")
        ir.add_gate(Ry(Qubit(0), Float(math.pi / 2)))
        ir.add_gate(Rx(Qubit(0), Float(math.pi)))
        ir.add_gate(Rz(Qubit(1), Float(1.2345)))
        ir.add_gate(Ry(Qubit(2), Float(1)))
        ir.add_gate(Ry(Qubit(2), Float(3.234)))

        expected_ir = SquirrelIR(number_of_qubits=4, qubit_register_name="q")
        expected_ir.add_gate(
            BlochSphereRotation(qubit=Qubit(0), axis=(1, 0, 1), angle=math.pi)
        )  # This is hadamard with 0 phase...
        expected_ir.add_gate(Rz(Qubit(1), Float(1.2345)))
        expected_ir.add_gate(Ry(Qubit(2), Float(4.234)))

        self.modify_ir_and_check(ir, action=merger.merge_single_qubit_gates, expected_ir=expected_ir)

        self.assertTrue(ir.statements[0].is_anonymous)  # When fusion happens, the resulting gate is anonymous.
        self.assertEqual(ir.statements[1].generator, Rz)  # Otherwise it keeps the same generator and arguments.
        self.assertEqual(ir.statements[1].arguments, (Qubit(1), Float(1.2345)))
        self.assertTrue(ir.statements[2].is_anonymous)

    def test_merge_and_flush(self):
        ir = SquirrelIR(number_of_qubits=4, qubit_register_name="q")
        ir.add_gate(Ry(Qubit(0), Float(math.pi / 2)))
        ir.add_gate(Rz(Qubit(1), Float(1.5)))
        ir.add_gate(Rx(Qubit(0), Float(math.pi)))
        ir.add_gate(Rz(Qubit(1), Float(-2.5)))
        ir.add_gate(CNOT(Qubit(0), Qubit(1)))
        ir.add_gate(Ry(Qubit(0), Float(3.234)))

        expected_ir = SquirrelIR(number_of_qubits=4, qubit_register_name="q")
        expected_ir.add_gate(
            BlochSphereRotation(qubit=Qubit(0), axis=(1, 0, 1), angle=math.pi)
        )  # This is hadamard with 0 phase...
        expected_ir.add_gate(Rz(Qubit(1), Float(-1.0)))
        expected_ir.add_gate(CNOT(Qubit(0), Qubit(1)))
        expected_ir.add_gate(Ry(Qubit(0), Float(3.234)))

        self.modify_ir_and_check(ir, action=merger.merge_single_qubit_gates, expected_ir=expected_ir)

        self.assertTrue(ir.statements[0].is_anonymous)
        self.assertEqual(ir.statements[3].generator, Ry)
        self.assertEqual(ir.statements[3].arguments, (Qubit(0), Float(3.234)))


if __name__ == "__main__":
    unittest.main()
