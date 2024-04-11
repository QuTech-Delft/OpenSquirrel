import unittest
from test.ir_equality_test_base import IREqualityTestBase

from opensquirrel.decompose.mckay_decomposer import McKayDecomposer
from opensquirrel.default_gates import *
from opensquirrel.squirrel_ir import Float, Qubit


class DecomposeMcKayTests(IREqualityTestBase):
    def test_ignores_2q_gates(self):
        self.assertEqual(McKayDecomposer.decompose(CNOT(Qubit(0), Qubit(1))), [CNOT(Qubit(0), Qubit(1))])
        self.assertEqual(
            McKayDecomposer.decompose(CR(Qubit(2), Qubit(3), Float(2.123))), [CR(Qubit(2), Qubit(3), Float(2.123))]
        )

    def test_identity_empty_decomposition(self):
        self.assertEqual(McKayDecomposer.decompose(BlochSphereRotation.identity(Qubit(0))), [])

    def test_x(self):
        self.assertEqual(
            McKayDecomposer.decompose(X(Qubit(0))),
            [
                # FIXME: we can do better here. See https://github.com/QuTech-Delft/OpenSquirrel/issues/89.
                Rz(Qubit(0), Float(-math.pi / 2)),
                X90(Qubit(0)),
                X90(Qubit(0)),
                Rz(Qubit(0), Float(-math.pi / 2)),
            ],
        )

    def test_y(self):
        self.assertEqual(
            McKayDecomposer.decompose(Y(Qubit(0))), [Rz(Qubit(0), Float(math.pi)), X90(Qubit(0)), X90(Qubit(0))]
        )

    def test_z(self):
        self.assertEqual(
            McKayDecomposer.decompose(Z(Qubit(0))),
            [
                Rz(Qubit(0), Float(-math.pi / 2)),
                X90(Qubit(0)),
                Rz(Qubit(0), Float(math.pi)),
                X90(Qubit(0)),
                Rz(Qubit(0), Float(math.pi / 2)),
            ],
        )

    def test_hadamard(self):
        self.assertEqual(
            McKayDecomposer.decompose(H(Qubit(0))),
            [
                BlochSphereRotation(Qubit(0), axis=(1, 0, 0), angle=math.pi / 2, phase=0.0),
                BlochSphereRotation(Qubit(0), axis=(0, 0, 1), angle=math.pi / 2, phase=0.0),
                BlochSphereRotation(Qubit(0), axis=(1, 0, 0), angle=math.pi / 2, phase=0.0),
            ],
        )

    def test_arbitrary(self):
        self.assertEqual(
            McKayDecomposer.decompose(BlochSphereRotation(qubit=Qubit(0), angle=5.21, axis=(1, 2, 3), phase=0.324)),
            [
                Rz(Qubit(0), Float(0.018644578210707863)),
                X90(Qubit(0)),
                Rz(Qubit(0), Float(2.520651583905213)),
                X90(Qubit(0)),
                Rz(Qubit(0), Float(2.2329420137988887)),
            ],
        )


if __name__ == "__main__":
    unittest.main()
