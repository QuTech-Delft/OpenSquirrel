import unittest

from opensquirrel.circuit import Circuit
from opensquirrel.decomposer import general_decomposer
from opensquirrel.decomposer.general_decomposer import Decomposer, check_gate_replacement
from opensquirrel.default_gates import *
from opensquirrel.register_manager import RegisterManager
from opensquirrel.squirrel_ir import Comment, Qubit, SquirrelIR


class ReplacerTest(unittest.TestCase):
    @staticmethod
    def test_check_valid_replacement():
        check_gate_replacement(BlochSphereRotation.identity(Qubit(0)), [BlochSphereRotation.identity(Qubit(0))])

        check_gate_replacement(
            BlochSphereRotation.identity(Qubit(0)),
            [BlochSphereRotation.identity(Qubit(0)), BlochSphereRotation.identity(Qubit(0))],
        )

        check_gate_replacement(BlochSphereRotation.identity(Qubit(0)), [H(Qubit(0)), H(Qubit(0))])

        check_gate_replacement(H(Qubit(0)), [H(Qubit(0)), H(Qubit(0)), H(Qubit(0))])

        check_gate_replacement(
            CNOT(Qubit(0), Qubit(1)), [CNOT(Qubit(0), Qubit(1)), BlochSphereRotation.identity(Qubit(0))]
        )

        # Arbitrary global phase change is not considered an issue.
        check_gate_replacement(
            CNOT(Qubit(0), Qubit(1)),
            [CNOT(Qubit(0), Qubit(1)), BlochSphereRotation(Qubit(0), angle=0, axis=(1, 0, 0), phase=621.6546)],
        )

    def test_check_valid_replacement_wrong_qubit(self):
        with self.assertRaisesRegex(Exception, r"Replacement for gate H does not seem to operate on the right qubits"):
            check_gate_replacement(H(Qubit(0)), [H(Qubit(1))])

        with self.assertRaisesRegex(
            Exception, r"Replacement for gate CNOT does not seem to operate on the right qubits"
        ):
            check_gate_replacement(CNOT(Qubit(0), Qubit(1)), [CNOT(Qubit(2), Qubit(1))])

        with self.assertRaisesRegex(Exception, r"Replacement for gate CNOT does not preserve the quantum state"):
            check_gate_replacement(CNOT(Qubit(0), Qubit(1)), [CNOT(Qubit(1), Qubit(0))])

    def test_check_valid_replacement_cnot_as_sqrt_swap(self):
        # https://en.wikipedia.org/wiki/Quantum_logic_gate#/media/File:Qcircuit_CNOTsqrtSWAP2.svg
        c = Qubit(0)
        t = Qubit(1)
        check_gate_replacement(
            CNOT(control=c, target=t),
            [
                Ry(t, Float(math.pi / 2)),
                sqrtSWAP(c, t),
                Z(c),
                sqrtSWAP(c, t),
                Rz(c, Float(-math.pi / 2)),
                Rz(t, Float(-math.pi / 2)),
                Ry(t, Float(-math.pi / 2)),
            ],
        )

        with self.assertRaisesRegex(Exception, r"Replacement for gate CNOT does not preserve the quantum state"):
            check_gate_replacement(
                CNOT(control=c, target=t),
                [
                    Ry(t, Float(math.pi / 2)),
                    sqrtSWAP(c, t),
                    Z(c),
                    sqrtSWAP(c, t),
                    Rz(c, Float(-math.pi / 2 + 0.01)),
                    Rz(t, Float(-math.pi / 2)),
                    Ry(t, Float(-math.pi / 2)),
                ],
            )

        with self.assertRaisesRegex(
            Exception, r"Replacement for gate CNOT does not seem to operate on the right qubits"
        ):
            check_gate_replacement(
                CNOT(control=c, target=t),
                [
                    Ry(t, Float(math.pi / 2)),
                    sqrtSWAP(c, t),
                    Z(c),
                    sqrtSWAP(c, Qubit(2)),
                    Rz(c, Float(-math.pi / 2 + 0.01)),
                    Rz(t, Float(-math.pi / 2)),
                    Ry(t, Float(-math.pi / 2)),
                ],
            )

    def test_check_valid_replacement_large_number_of_qubits(self):
        # If we were building the whole circuit matrix, this would run out of memory.
        check_gate_replacement(H(Qubit(9234687)), [Y90(Qubit(9234687)), X(Qubit(9234687))])

        with self.assertRaisesRegex(Exception, r"Replacement for gate H does not seem to operate on the right qubits"):
            check_gate_replacement(H(Qubit(9234687)), [Y90(Qubit(698446519)), X(Qubit(9234687))])

        with self.assertRaisesRegex(Exception, r"Replacement for gate H does not preserve the quantum state"):
            check_gate_replacement(H(Qubit(9234687)), [Y90(Qubit(9234687)), X(Qubit(9234687)), X(Qubit(9234687))])

    def test_replace_generic(self):
        register_manager = RegisterManager(qubit_register_size=3)
        squirrel_ir = SquirrelIR()
        squirrel_ir.add_gate(H(Qubit(0)))
        squirrel_ir.add_gate(CNOT(Qubit(0), Qubit(1)))
        circuit = Circuit(register_manager, squirrel_ir)

        # A simple decomposer function that adds identities before and after single-qubit gates.
        class TestDecomposer(Decomposer):
            def decompose(self, g: Gate) -> [Gate]:
                if isinstance(g, BlochSphereRotation):
                    return [BlochSphereRotation.identity(g.qubit), g, BlochSphereRotation.identity(g.qubit)]
                return [g]

        general_decomposer.decompose(squirrel_ir, decomposer=TestDecomposer())

        expected_ir = SquirrelIR()
        expected_ir.add_gate(BlochSphereRotation.identity(Qubit(0)))
        expected_ir.add_gate(H(Qubit(0)))
        expected_ir.add_gate(BlochSphereRotation.identity(Qubit(0)))
        expected_ir.add_gate(CNOT(Qubit(0), Qubit(1)))
        expected_circuit = Circuit(register_manager, expected_ir)

        self.assertEqual(expected_circuit, circuit)

    def test_replace(self):
        register_manager = RegisterManager(qubit_register_size=3)
        squirrel_ir = SquirrelIR()
        squirrel_ir.add_gate(H(Qubit(0)))
        squirrel_ir.add_comment(Comment("Test comment."))
        circuit = Circuit(register_manager, squirrel_ir)

        general_decomposer.replace(squirrel_ir, H, lambda q: [Y90(q), X(q)])

        expected_ir = SquirrelIR()
        expected_ir.add_gate(Y90(Qubit(0)))
        expected_ir.add_gate(X(Qubit(0)))
        expected_ir.add_comment(Comment("Test comment."))
        expected_circuit = Circuit(register_manager, expected_ir)

        self.assertEqual(expected_circuit, circuit)


if __name__ == "__main__":
    unittest.main()
