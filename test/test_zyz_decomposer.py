import unittest
from test.ir_equality_test_base import IREqualityTestBase

from opensquirrel.decomposer.zyz_decomposer import ZYZDecomposer
from opensquirrel.default_gates import *
from opensquirrel.squirrel_ir import Float, Qubit


class ZYZDecomposerTest(IREqualityTestBase):
    def test_ignores_2q_gates(self):
        self.assertEqual(ZYZDecomposer().decompose(CNOT(Qubit(0), Qubit(1))), [CNOT(Qubit(0), Qubit(1))])
        self.assertEqual(
            ZYZDecomposer().decompose(CR(Qubit(2), Qubit(3), Float(2.123))), [CR(Qubit(2), Qubit(3), Float(2.123))]
        )

    def test_identity_empty_decomposition(self):
        self.assertEqual(ZYZDecomposer().decompose(BlochSphereRotation.identity(Qubit(0))), [])

    def test_x(self):
        self.assertEqual(
            ZYZDecomposer().decompose(X(Qubit(0))),
            [
                S(Qubit(0)),
                Ry(Qubit(0), Float(math.pi)),
                Sdag(Qubit(0)),
            ],
        )

    def test_x_arbitrary(self):
        self.assertEqual(
            ZYZDecomposer().decompose(Rx(Qubit(0), Float(0.9))),
            [
                S(Qubit(0)),
                Ry(Qubit(0), Float(0.9)),
                Sdag(Qubit(0)),
            ],
        )

    def test_y(self):
        self.assertEqual(
            ZYZDecomposer().decompose(Y(Qubit(0))),
            [
                Ry(Qubit(0), Float(math.pi)),
            ],
        )

    def test_y_arbitrary(self):
        self.assertEqual(
            ZYZDecomposer().decompose(Ry(Qubit(0), Float(0.9))),
            [
                Ry(Qubit(0), Float(0.9)),
            ],
        )

    def test_z(self):
        self.assertEqual(
            ZYZDecomposer().decompose(Z(Qubit(0))),
            [
                Rz(Qubit(0), Float(math.pi)),
            ],
        )

    def test_z_arbitrary(self):
        self.assertEqual(
            ZYZDecomposer().decompose(Rz(Qubit(0), Float(0.123))),
            [
                Rz(Qubit(0), Float(0.123)),
            ],
        )

    def test_hadamard(self):
        self.assertEqual(
            ZYZDecomposer().decompose(H(Qubit(0))),
            [
                Rz(Qubit(0), Float(math.pi)),
                Ry(Qubit(0), Float(math.pi / 2)),
            ],
        )

    def test_arbitrary(self):
        self.assertEqual(
            ZYZDecomposer().decompose(BlochSphereRotation(qubit=Qubit(0), angle=5.21, axis=(1, 2, 3), phase=0.324)),
            [
                Rz(Qubit(0), Float(0.018644578210710527)),
                Ry(Qubit(0), Float(-0.6209410696845807)),
                Rz(Qubit(0), Float(-0.9086506397909061)),
            ],
        )


if __name__ == "__main__":
    unittest.main()
