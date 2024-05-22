import unittest
from test.ir_equality_test_base import IREqualityTestBase

from open_squirrel.decomposer.cnot_decomposer import CNOTDecomposer
from open_squirrel.default_gates import *
from open_squirrel.ir import Float, Qubit


class CNOTDecomposerTest(IREqualityTestBase):
    def test_ignores_1q_gates(self):
        self.assertEqual(CNOTDecomposer.decompose(H(Qubit(0))), [H(Qubit(0))])
        self.assertEqual(CNOTDecomposer.decompose(Rz(Qubit(0), Float(2.345))), [Rz(Qubit(0), Float(2.345))])

    def test_ignores_matrix_gate(self):
        self.assertEqual(CNOTDecomposer.decompose(SWAP(Qubit(4), Qubit(3))), [SWAP(Qubit(4), Qubit(3))])

    def test_ignores_double_controlled(self):
        g = ControlledGate(
            control_qubit=Qubit(5), target_gate=ControlledGate(control_qubit=Qubit(2), target_gate=X(Qubit(0)))
        )
        self.assertEqual(CNOTDecomposer.decompose(g), [g])

    def test_CNOT(self):
        self.assertEqual(
            CNOTDecomposer.decompose(CNOT(Qubit(0), Qubit(1))),
            [CNOT(Qubit(0), Qubit(1))],
        )

    def test_CZ(self):
        self.assertEqual(
            CNOTDecomposer.decompose(CZ(Qubit(0), Qubit(1))),
            [
                Rz(Qubit(1), Float(math.pi)),
                Ry(Qubit(1), Float(math.pi / 2)),
                CNOT(Qubit(0), Qubit(1)),
                Ry(Qubit(1), Float(-math.pi / 2)),
                Rz(Qubit(1), Float(math.pi)),
            ],
        )


if __name__ == "__main__":
    unittest.main()
