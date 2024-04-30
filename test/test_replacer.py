import unittest

from opensquirrel.decomposer import general_decomposer
from opensquirrel.decomposer.general_decomposer import Decomposer, check_valid_replacement
from opensquirrel.default_gates import *
from opensquirrel.squirrel_ir import Comment, Qubit, SquirrelIR


class ReplacerTest(unittest.TestCase):
    @staticmethod
    def test_check_valid_replacement():
        check_valid_replacement(BlochSphereRotation.identity(Qubit(0)), [BlochSphereRotation.identity(Qubit(0))])

        check_valid_replacement(
            BlochSphereRotation.identity(Qubit(0)),
            [BlochSphereRotation.identity(Qubit(0)), BlochSphereRotation.identity(Qubit(0))],
        )

        check_valid_replacement(BlochSphereRotation.identity(Qubit(0)), [H(Qubit(0)), H(Qubit(0))])

        check_valid_replacement(H(Qubit(0)), [H(Qubit(0)), H(Qubit(0)), H(Qubit(0))])

        check_valid_replacement(
            CNOT(Qubit(0), Qubit(1)), [CNOT(Qubit(0), Qubit(1)), BlochSphereRotation.identity(Qubit(0))]
        )

        # Arbitrary global phase change is not considered an issue.
        check_valid_replacement(
            CNOT(Qubit(0), Qubit(1)),
            [CNOT(Qubit(0), Qubit(1)), BlochSphereRotation(Qubit(0), angle=0, axis=(1, 0, 0), phase=621.6546)],
        )

    def test_check_valid_replacement_wrong_qubit(self):
        with self.assertRaisesRegex(Exception, r"Replacement for gate H does not seem to operate on the right qubits"):
            check_valid_replacement(H(Qubit(0)), [H(Qubit(1))])

        with self.assertRaisesRegex(
            Exception, r"Replacement for gate CNOT does not seem to operate on the right qubits"
        ):
            check_valid_replacement(CNOT(Qubit(0), Qubit(1)), [CNOT(Qubit(2), Qubit(1))])

        with self.assertRaisesRegex(Exception, r"Replacement for gate CNOT does not preserve the quantum state"):
            check_valid_replacement(CNOT(Qubit(0), Qubit(1)), [CNOT(Qubit(1), Qubit(0))])

    def test_check_valid_replacement_cnot_as_sqrt_swap(self):
        # https://en.wikipedia.org/wiki/Quantum_logic_gate#/media/File:Qcircuit_CNOTsqrtSWAP2.svg
        c = Qubit(0)
        t = Qubit(1)
        check_valid_replacement(
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
            check_valid_replacement(
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
            check_valid_replacement(
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
        check_valid_replacement(H(Qubit(9234687)), [Y90(Qubit(9234687)), X(Qubit(9234687))])

        with self.assertRaisesRegex(Exception, r"Replacement for gate H does not seem to operate on the right qubits"):
            check_valid_replacement(H(Qubit(9234687)), [Y90(Qubit(698446519)), X(Qubit(9234687))])

        with self.assertRaisesRegex(Exception, r"Replacement for gate H does not preserve the quantum state"):
            check_valid_replacement(H(Qubit(9234687)), [Y90(Qubit(9234687)), X(Qubit(9234687)), X(Qubit(9234687))])

    def test_replace_generic(self):
        squirrel_ir = SquirrelIR(qubit_register_size=3, qubit_register_name="test")

        squirrel_ir.add_gate(H(Qubit(0)))
        squirrel_ir.add_gate(CNOT(Qubit(0), Qubit(1)))

        # A simple decomposer function that adds identities before and after single-qubit gates.
        class TestDecomposer(Decomposer):
            def decompose(self, g: Gate) -> [Gate]:
                if isinstance(g, BlochSphereRotation):
                    return [BlochSphereRotation.identity(g.qubit), g, BlochSphereRotation.identity(g.qubit)]

                return [g]

        general_decomposer.decompose(squirrel_ir, decomposer=TestDecomposer())

        expected_ir = SquirrelIR(qubit_register_size=3, qubit_register_name="test")

        expected_ir.add_gate(BlochSphereRotation.identity(Qubit(0)))
        expected_ir.add_gate(H(Qubit(0)))
        expected_ir.add_gate(BlochSphereRotation.identity(Qubit(0)))
        expected_ir.add_gate(CNOT(Qubit(0), Qubit(1)))

        self.assertEqual(expected_ir, squirrel_ir)

    def test_replace(self):
        squirrel_ir = SquirrelIR(qubit_register_size=3, qubit_register_name="test")

        squirrel_ir.add_gate(H(Qubit(0)))
        squirrel_ir.add_comment(Comment("Test comment."))

        general_decomposer.replace(squirrel_ir, H, lambda q: [Y90(q), X(q)])

        expected_ir = SquirrelIR(qubit_register_size=3, qubit_register_name="test")

        expected_ir.add_gate(Y90(Qubit(0)))
        expected_ir.add_gate(X(Qubit(0)))
        expected_ir.add_comment(Comment("Test comment."))

        self.assertEqual(expected_ir, squirrel_ir)


if __name__ == "__main__":
    unittest.main()
