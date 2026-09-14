import numpy as np
import pytest
from numpy.typing import ArrayLike

from opensquirrel.ir import IRVisitor
from opensquirrel.ir.semantics import MatrixGateSemantic
from opensquirrel.ir.two_qubit_gate import TwoQubitGate


class TestMatrixGateSemantic:
    @pytest.fixture
    def gate(self) -> TwoQubitGate:
        cnot_matrix = [
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1],
            [0, 0, 1, 0],
        ]
        return TwoQubitGate(42, 100, gate_semantic=MatrixGateSemantic(cnot_matrix))

    def test_array_like(self) -> None:
        gate = TwoQubitGate(
            0, 1, gate_semantic=MatrixGateSemantic([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]])
        )
        assert repr(gate) == (
            "TwoQubitGate(qubits=[(Qubit[0], Qubit[1])], gate_semantic=MatrixGateSemantic(matrix="
            "[[1.+0.j 0.+0.j 0.+0.j 0.+0.j] [0.+0.j 1.+0.j 0.+0.j 0.+0.j] "
            "[0.+0.j 0.+0.j 0.+0.j 1.+0.j] [0.+0.j 0.+0.j 1.+0.j 0.+0.j]]))"
        )

    def test_incorrect_array(self) -> None:
        with pytest.raises(ValueError, match=r".* inhomogeneous shape after .*") as e_info:
            TwoQubitGate(0, 1, gate_semantic=MatrixGateSemantic([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 0]]))
        assert "setting an array element with a sequence." in str(e_info.value)

    def test_repr(self, gate: TwoQubitGate) -> None:
        assert repr(gate) == (
            "TwoQubitGate(qubits=[(Qubit[42], Qubit[100])], gate_semantic=MatrixGateSemantic(matrix="
            "[[1.+0.j 0.+0.j 0.+0.j 0.+0.j] [0.+0.j 1.+0.j 0.+0.j 0.+0.j] "
            "[0.+0.j 0.+0.j 0.+0.j 1.+0.j] [0.+0.j 0.+0.j 1.+0.j 0.+0.j]]))"
        )

    def test_is_identity(self, gate: TwoQubitGate) -> None:
        assert TwoQubitGate(42, 100, gate_semantic=MatrixGateSemantic(np.eye(4, dtype=np.complex128))).is_identity()
        assert not gate.is_identity()

    @pytest.mark.parametrize(
        ("matrix", "error_msg"),
        [
            ([[1, 0, 0], [0, 1, 0]], "number of rows should be equal to the number of columns"),
            (np.eye(3), "number of rows/columns should be a power of 2"),
        ],
        ids=["not-square", "not-a-power-of-2"],
    )
    def test_incorrect_shape(self, matrix: ArrayLike, error_msg: str) -> None:
        with pytest.raises(ValueError, match=error_msg):
            MatrixGateSemantic(matrix)

    def test_accept(self) -> None:
        class Visitor(IRVisitor):
            def visit_matrix_gate_semantic(self, matrix: MatrixGateSemantic) -> MatrixGateSemantic:
                return matrix

        semantic = MatrixGateSemantic(np.eye(4))
        assert semantic.accept(Visitor()) is semantic
