import unittest
from test.ir_equality_test_base import IREqualityTestBase

from opensquirrel.default_gates import *
from opensquirrel.squirrel_ir import Float, Qubit, SquirrelIR
from opensquirrel.zyz_decomposer import ZYZDecomposer


class ZYZDecomposerTest(IREqualityTestBase):
    def test_ignores_2q_gates(self):
        self.assertEqual(ZYZDecomposer.decompose(cnot(Qubit(0), Qubit(1))), [cnot(Qubit(0), Qubit(1))])
        self.assertEqual(
            ZYZDecomposer.decompose(cr(Qubit(2), Qubit(3), Float(2.123))), [cr(Qubit(2), Qubit(3), Float(2.123))]
        )

    def test_identity_empty_decomposition(self):
        self.assertEqual(ZYZDecomposer.decompose(BlochSphereRotation.identity(Qubit(0))), [])

    def test_x(self):
        self.assertEqual(
            ZYZDecomposer.decompose(x(Qubit(0))),
            [
                z90(Qubit(0)),
                ry(Qubit(0), Float(math.pi)),
                zm90(Qubit(0)),
            ],
        )

    def test_x_arbitrary(self):
        self.assertEqual(
            ZYZDecomposer.decompose(rx(Qubit(0), Float(0.9))),
            [
                z90(Qubit(0)),
                ry(Qubit(0), Float(0.9)),
                zm90(Qubit(0)),
            ],
        )

    def test_y(self):
        self.assertEqual(
            ZYZDecomposer.decompose(y(Qubit(0))),
            [
                ry(Qubit(0), Float(math.pi)),
            ],
        )

    def test_y_arbitrary(self):
        self.assertEqual(
            ZYZDecomposer.decompose(ry(Qubit(0), Float(0.9))),
            [
                ry(Qubit(0), Float(0.9)),
            ],
        )

    def test_z(self):
        self.assertEqual(
            ZYZDecomposer.decompose(z(Qubit(0))),
            [
                rz(Qubit(0), Float(math.pi)),
            ],
        )

    def test_z_arbitrary(self):
        self.assertEqual(
            ZYZDecomposer.decompose(rz(Qubit(0), Float(0.123))),
            [
                rz(Qubit(0), Float(0.123)),
            ],
        )

    def test_hadamard(self):
        self.assertEqual(
            ZYZDecomposer.decompose(h(Qubit(0))),
            [
                rz(Qubit(0), Float(math.pi)),
                ry(Qubit(0), Float(math.pi / 2)),
            ],
        )

    def test_arbitrary(self):
        self.assertEqual(
            ZYZDecomposer.decompose(BlochSphereRotation(qubit=Qubit(0), angle=5.21, axis=(1, 2, 3), phase=0.324)),
            [
                rz(Qubit(0), Float(0.018644578210710527)),
                ry(Qubit(0), Float(-0.6209410696845807)),
                rz(Qubit(0), Float(-0.9086506397909061)),
            ],
        )


if __name__ == "__main__":
    unittest.main()
