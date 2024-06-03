import unittest
from test.ir_equality_test_base import IREqualityTestBase

from opensquirrel.decomposer.xyx_decomposer import XYXDecomposer
from opensquirrel.default_gates import *
from opensquirrel.ir import Float, Qubit


class ZYZDecomposerTest(IREqualityTestBase):

    def test_hadamard(self):
        self.assertEqual(
            XYXDecomposer.decompose(H(Qubit(0))),
            [
                Rx(Qubit(0), Float(math.pi)),
                Ry(Qubit(0), Float(math.pi / 2)),
            ],
        )

    def test_s_gate(self):
        self.assertEqual(
            XYXDecomposer.decompose(S(Qubit(0))),
            [
                Rx(Qubit(0), Float(math.pi / 2)),
                Ry(Qubit(0), Float(math.pi / 2)),
                Rx(Qubit(0), Float(- math.pi / 2))
            ],
        )

    def test_arbitrary(self):
        self.assertEqual(
            XYXDecomposer.decompose(BlochSphereRotation(qubit=Qubit(0), angle=5.21, axis=(1, 2, 3), phase=0.324)),
            [
                Rx(Qubit(0), Float(0.8251439260060653)),
                Ry(Qubit(0), Float(-1.030183660156084)),
                Rx(Qubit(0), Float(-1.140443520488592)),
            ],
        )

    def test_x_gate(self):
        self.assertEqual(
            XYXDecomposer.decompose(X(Qubit(0))),
            [
                Rx(Qubit(0), Float(math.pi)),
            ],
        )

    def test_y_arbitrary(self):
        self.assertEqual(
            XYXDecomposer.decompose(Ry(Qubit(0), Float(0.9))),
            [
                Ry(Qubit(0), Float(0.9)),
            ],
        )

    def test_y(self):
        self.assertEqual(
            XYXDecomposer.decompose(Y(Qubit(0))),
            [
                Ry(Qubit(0), Float(math.pi)),
            ],
        )

if __name__ == "__main__":
    unittest.main()
