import numpy as np
import pytest

from opensquirrel.ir import Qubit
from opensquirrel.ir.semantics import BlochSphereRotation, CanonicalGateSemantic, MatrixGateSemantic
from opensquirrel.ir.two_qubit_gate import TwoQubitGate
from opensquirrel.utils.matrix_expander import can2


class TestTwoQubitGate:
    @pytest.fixture
    def gate(self) -> TwoQubitGate:
        cnot_matrix = [
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1],
            [0, 0, 1, 0],
        ]
        return TwoQubitGate(42, 100, gate_semantic=MatrixGateSemantic(cnot_matrix))

    def test_qubit_operands(self, gate: TwoQubitGate) -> None:
        assert gate.qubit_operands == (Qubit(42), Qubit(100))

    def test_same_qubits(self) -> None:
        with pytest.raises(ValueError, match="qubit operands cannot be the same qubit"):
            TwoQubitGate(0, 0, gate_semantic=MatrixGateSemantic(np.eye(4, dtype=np.complex128)))

    def test_matrix_gate_to_canonical_conversion(self, gate: TwoQubitGate) -> None:
        canonical = gate.canonical
        assert isinstance(canonical, CanonicalGateSemantic)
        assert canonical.axis is not None
        assert canonical.rotations is not None
        assert len(canonical.rotations) == 4

        assert all(isinstance(rot, BlochSphereRotation) for rot in canonical.rotations)

    def test_canonical_gate_to_matrix_conversion(self) -> None:
        gate = TwoQubitGate(0, 1, gate_semantic=CanonicalGateSemantic((0, 0, 0)))
        matrix = gate.matrix
        assert isinstance(matrix, MatrixGateSemantic)
        assert matrix.is_identity()

    def test_canonical_non_trivial_to_matrix_conversion(self) -> None:
        axis = (1 / 2, 0, 0)
        gate = TwoQubitGate(0, 1, gate_semantic=CanonicalGateSemantic(axis))

        matrix = gate.matrix
        assert isinstance(matrix, MatrixGateSemantic)

        expected_matrix = can2(axis)
        np.testing.assert_almost_equal(matrix.matrix, expected_matrix)

    def test_canonical_gate_semantic_with_rotations(self) -> None:
        from opensquirrel.utils.matrix_expander import can1

        rotations = [
            BlochSphereRotation(axis=(1, 0, 0), angle=np.pi / 4, phase=0),
            BlochSphereRotation(axis=(0, 1, 0), angle=np.pi / 2, phase=np.pi / 4),
            BlochSphereRotation(axis=(0, 0, 1), angle=np.pi / 3, phase=np.pi / 6),
            BlochSphereRotation(axis=(1, 1, 0), angle=np.pi / 6, phase=0),
        ]

        axis = (1 / 4, 0, 0)
        canonical_semantic = CanonicalGateSemantic(axis, rotations)
        gate = TwoQubitGate(0, 1, gate_semantic=canonical_semantic)

        matrix = gate.matrix
        assert isinstance(matrix, MatrixGateSemantic)

        k1 = can1(rotations[0].axis, rotations[0].angle, rotations[0].phase)
        k2 = can1(rotations[1].axis, rotations[1].angle, rotations[1].phase)
        k3 = can1(rotations[2].axis, rotations[2].angle, rotations[2].phase)
        k4 = can1(rotations[3].axis, rotations[3].angle, rotations[3].phase)

        expected_matrix = np.kron(k3, k4) @ can2(axis) @ np.kron(k1, k2)
        np.testing.assert_almost_equal(matrix.matrix, expected_matrix)

    def test_canonical_gate_identity_with_rotations(self) -> None:
        rotations = [
            BlochSphereRotation(axis=(1, 0, 0), angle=0, phase=0),
            BlochSphereRotation(axis=(0, 1, 0), angle=0, phase=0),
            BlochSphereRotation(axis=(0, 0, 1), angle=0, phase=0),
            BlochSphereRotation(axis=(1, 1, 0), angle=0, phase=0),
        ]

        canonical_semantic = CanonicalGateSemantic((0, 0, 0), rotations)
        gate = TwoQubitGate(0, 1, gate_semantic=canonical_semantic)

        assert gate.is_identity()
