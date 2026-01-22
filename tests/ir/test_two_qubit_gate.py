from math import pi

import numpy as np
import pytest

from opensquirrel.ir import Qubit
from opensquirrel.ir.semantics import BlochSphereRotation, ControlledGateSemantic, MatrixGateSemantic
from opensquirrel.ir.single_qubit_gate import SingleQubitGate
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
        with pytest.raises(ValueError, match="qubit0 and qubit1 cannot be the same"):
            TwoQubitGate(0, 0, gate_semantic=MatrixGateSemantic(np.eye(4, dtype=np.complex128)))

    def test_controlled_gate_with_mismatch_in_target_and_target_gate_qubit(self) -> None:
        with pytest.raises(ValueError, match="the qubit from the target gate does not match with 'qubit1'"):
            TwoQubitGate(
                0,
                1,
                gate_semantic=ControlledGateSemantic(
                    SingleQubitGate(0, BlochSphereRotation([0, 0, 1], angle=pi, phase=pi / 2))
                ),
            )
