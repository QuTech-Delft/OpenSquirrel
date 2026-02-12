import numpy as np
import pytest

from opensquirrel.ir import Qubit
from opensquirrel.ir.semantics import MatrixGateSemantic
from opensquirrel.ir.two_qubit_gate import TwoQubitGate


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
