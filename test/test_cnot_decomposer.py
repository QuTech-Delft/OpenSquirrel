import unittest
from test.ir_equality_test_base import IREqualityTestBase

from opensquirrel.cnot_decomposer import CNOTDecomposer
from opensquirrel.default_gates import *
from opensquirrel.squirrel_ir import Float, Qubit, SquirrelIR


class CNOTDecomposerTest(IREqualityTestBase):
    def test_ignores_1q_gates(self):
        self.assertEqual(CNOTDecomposer.decompose(h(Qubit(0))), [h(Qubit(0))])
        self.assertEqual(CNOTDecomposer.decompose(rz(Qubit(0), Float(2.345))), [rz(Qubit(0), Float(2.345))])

    def test_ignores_matrix_gate(self):
        self.assertEqual(CNOTDecomposer.decompose(swap(Qubit(4), Qubit(3))), [swap(Qubit(4), Qubit(3))])

    def test_ignores_double_controlled(self):
        g = ControlledGate(
            control_qubit=Qubit(5), target_gate=ControlledGate(control_qubit=Qubit(2), target_gate=x(Qubit(0)))
        )
        self.assertEqual(CNOTDecomposer.decompose(g), [g])

    def test_cnot(self):
        self.assertEqual(
            CNOTDecomposer.decompose(cnot(Qubit(0), Qubit(1))),
            [cnot(Qubit(0), Qubit(1))],
        )

    def test_cz(self):
        self.assertEqual(
            CNOTDecomposer.decompose(cz(Qubit(0), Qubit(1))),
            [
                rz(Qubit(1), Float(math.pi)),
                ry(Qubit(1), Float(math.pi / 2)),
                cnot(Qubit(0), Qubit(1)),
                ry(Qubit(1), Float(-math.pi / 2)),
                rz(Qubit(1), Float(math.pi)),
            ],
        )


if __name__ == "__main__":
    unittest.main()
