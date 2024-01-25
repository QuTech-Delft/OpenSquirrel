import unittest

from opensquirrel import replacer
from opensquirrel.default_gates import *
from opensquirrel.replacer import Decomposer, check_valid_replacement
from opensquirrel.squirrel_ir import Qubit, SquirrelIR


class ReplacerTest(unittest.TestCase):
    @staticmethod
    def test_check_valid_replacement():
        check_valid_replacement(BlochSphereRotation.identity(Qubit(0)), [BlochSphereRotation.identity(Qubit(0))])

        check_valid_replacement(
            BlochSphereRotation.identity(Qubit(0)),
            [BlochSphereRotation.identity(Qubit(0)), BlochSphereRotation.identity(Qubit(0))],
        )

        check_valid_replacement(BlochSphereRotation.identity(Qubit(0)), [h(Qubit(0)), h(Qubit(0))])

        check_valid_replacement(h(Qubit(0)), [h(Qubit(0)), h(Qubit(0)), h(Qubit(0))])

        check_valid_replacement(
            cnot(Qubit(0), Qubit(1)), [cnot(Qubit(0), Qubit(1)), BlochSphereRotation.identity(Qubit(0))]
        )

        # Arbitrary global phase change is not considered an issue.
        check_valid_replacement(
            cnot(Qubit(0), Qubit(1)),
            [cnot(Qubit(0), Qubit(1)), BlochSphereRotation(Qubit(0), angle=0, axis=(1, 0, 0), phase=621.6546)],
        )

    def test_check_valid_replacement_wrong_qubit(self):
        with self.assertRaisesRegex(Exception, r"Replacement for gate h does not seem to operate on the right qubits"):
            check_valid_replacement(h(Qubit(0)), [h(Qubit(1))])

        with self.assertRaisesRegex(
            Exception, r"Replacement for gate cnot does not seem to operate on the right qubits"
        ):
            check_valid_replacement(cnot(Qubit(0), Qubit(1)), [cnot(Qubit(2), Qubit(1))])

        with self.assertRaisesRegex(Exception, r"Replacement for gate cnot does not preserve the quantum state"):
            check_valid_replacement(cnot(Qubit(0), Qubit(1)), [cnot(Qubit(1), Qubit(0))])

    def test_check_valid_replacement_cnot_as_sqrt_swap(self):
        # https://en.wikipedia.org/wiki/Quantum_logic_gate#/media/File:Qcircuit_CNOTsqrtSWAP2.svg
        c = Qubit(0)
        t = Qubit(1)
        check_valid_replacement(
            cnot(control=c, target=t),
            [
                ry(t, Float(math.pi / 2)),
                sqrt_swap(c, t),
                z(c),
                sqrt_swap(c, t),
                rz(c, Float(-math.pi / 2)),
                rz(t, Float(-math.pi / 2)),
                ry(t, Float(-math.pi / 2)),
            ],
        )

        with self.assertRaisesRegex(Exception, r"Replacement for gate cnot does not preserve the quantum state"):
            check_valid_replacement(
                cnot(control=c, target=t),
                [
                    ry(t, Float(math.pi / 2)),
                    sqrt_swap(c, t),
                    z(c),
                    sqrt_swap(c, t),
                    rz(c, Float(-math.pi / 2 + 0.01)),
                    rz(t, Float(-math.pi / 2)),
                    ry(t, Float(-math.pi / 2)),
                ],
            )

        with self.assertRaisesRegex(
            Exception, r"Replacement for gate cnot does not seem to operate on the right qubits"
        ):
            check_valid_replacement(
                cnot(control=c, target=t),
                [
                    ry(t, Float(math.pi / 2)),
                    sqrt_swap(c, t),
                    z(c),
                    sqrt_swap(c, Qubit(2)),
                    rz(c, Float(-math.pi / 2 + 0.01)),
                    rz(t, Float(-math.pi / 2)),
                    ry(t, Float(-math.pi / 2)),
                ],
            )

    def test_check_valid_replacement_large_number_of_qubits(self):
        # If we were building the whole circuit matrix, this would run out of memory.
        check_valid_replacement(h(Qubit(9234687)), [y90(Qubit(9234687)), x(Qubit(9234687))])

        with self.assertRaisesRegex(Exception, r"Replacement for gate h does not seem to operate on the right qubits"):
            check_valid_replacement(h(Qubit(9234687)), [y90(Qubit(698446519)), x(Qubit(9234687))])

        with self.assertRaisesRegex(Exception, r"Replacement for gate h does not preserve the quantum state"):
            check_valid_replacement(h(Qubit(9234687)), [y90(Qubit(9234687)), x(Qubit(9234687)), x(Qubit(9234687))])

    def test_replace_generic(self):
        squirrel_ir = SquirrelIR(number_of_qubits=3, qubit_register_name="test")

        squirrel_ir.add_gate(h(Qubit(0)))
        squirrel_ir.add_gate(cnot(Qubit(0), Qubit(1)))

        # A stupid replacer function that adds identities before and after single-qubit gates.
        class TestDecomposer(Decomposer):
            def decompose(self, g: Gate) -> [Gate]:
                if isinstance(g, BlochSphereRotation):
                    return [BlochSphereRotation.identity(g.qubit), g, BlochSphereRotation.identity(g.qubit)]

                return [g]

        replacer.decompose(squirrel_ir, decomposer=TestDecomposer())

        expected_ir = SquirrelIR(number_of_qubits=3, qubit_register_name="test")

        expected_ir.add_gate(BlochSphereRotation.identity(Qubit(0)))
        expected_ir.add_gate(h(Qubit(0)))
        expected_ir.add_gate(BlochSphereRotation.identity(Qubit(0)))
        expected_ir.add_gate(cnot(Qubit(0), Qubit(1)))

        self.assertEqual(expected_ir, squirrel_ir)

    def test_replace(self):
        squirrel_ir = SquirrelIR(number_of_qubits=3, qubit_register_name="test")

        squirrel_ir.add_gate(h(Qubit(0)))
        squirrel_ir.add_comment(Comment("Test comment."))

        replacer.replace(squirrel_ir, h, lambda q: [y90(q), x(q)])

        expected_ir = SquirrelIR(number_of_qubits=3, qubit_register_name="test")

        expected_ir.add_gate(y90(Qubit(0)))
        expected_ir.add_gate(x(Qubit(0)))
        expected_ir.add_comment(Comment("Test comment."))

        self.assertEqual(expected_ir, squirrel_ir)


if __name__ == "__main__":
    unittest.main()
