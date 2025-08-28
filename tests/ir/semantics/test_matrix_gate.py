import numpy as np
import pytest

from opensquirrel.ir import Qubit
from opensquirrel.ir.semantics import MatrixGate


class TestMatrixGate:
    @pytest.fixture
    def gate(self) -> MatrixGate:
        cnot_matrix = [
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1],
            [0, 0, 1, 0],
        ]
        return MatrixGate(cnot_matrix, operands=[42, 100])

    def test_array_like(self) -> None:
        gate = MatrixGate([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]], [0, 1])
        assert (
            repr(gate) == "MatrixGate(qubits=[Qubit[0], Qubit[1]], matrix=[[1.+0.j 0.+0.j 0.+0.j 0.+0.j] "
            "[0.+0.j 1.+0.j 0.+0.j 0.+0.j] [0.+0.j 0.+0.j 0.+0.j 1.+0.j] [0.+0.j 0.+0.j 1.+0.j 0.+0.j]])"
        )

    def test_incorrect_array(self) -> None:
        with pytest.raises(ValueError, match=r".* inhomogeneous shape after .*") as e_info:
            MatrixGate([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 0]], [0, 1])
        assert "setting an array element with a sequence." in str(e_info.value)

    def test_repr(self, gate: MatrixGate) -> None:
        assert (
            repr(gate) == "MatrixGate(qubits=[Qubit[42], Qubit[100]], matrix=[[1.+0.j 0.+0.j 0.+0.j 0.+0.j] "
            "[0.+0.j 1.+0.j 0.+0.j 0.+0.j] [0.+0.j 0.+0.j 0.+0.j 1.+0.j] [0.+0.j 0.+0.j 1.+0.j 0.+0.j]])"
        )

    def test_get_qubit_operands(self, gate: MatrixGate) -> None:
        assert gate.get_qubit_operands() == [Qubit(42), Qubit(100)]

    def test_is_identity(self, gate: MatrixGate) -> None:
        assert MatrixGate(np.eye(4, dtype=np.complex128), operands=[42, 100]).is_identity()
        assert not gate.is_identity()

    def test_matrix_gate_same_control_and_target_qubit(self) -> None:
        with pytest.raises(ValueError, match="operands cannot be the same"):
            MatrixGate(np.eye(4, dtype=np.complex128), [0, 0])
