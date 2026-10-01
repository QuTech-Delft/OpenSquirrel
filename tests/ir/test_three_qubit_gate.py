import numpy as np
import pytest

from opensquirrel import CCX, CSWAP
from opensquirrel.ir import Qubit
from opensquirrel.ir.semantics import CanonicalGateSemantic, MatrixGateSemantic
from opensquirrel.ir.three_qubit_gate import ThreeQubitGate
from opensquirrel.utils.matrix_expander import get_matrix


class TestThreeQubitGate:
    @pytest.fixture
    def gate(self) -> ThreeQubitGate:
        # The specific matrix is irrelevant here, as long as it is not the identity.
        ccz_matrix = np.diag([1, 1, 1, 1, 1, 1, 1, -1])
        return ThreeQubitGate(42, 100, 7, gate_semantic=MatrixGateSemantic(ccz_matrix))

    def test_qubit_operands(self, gate: ThreeQubitGate) -> None:
        assert gate.qubit_operands == (Qubit(42), Qubit(100), Qubit(7))

    def test_same_qubits(self) -> None:
        with pytest.raises(ValueError, match="qubit operands cannot be the same qubit"):
            ThreeQubitGate(0, 1, 0, gate_semantic=MatrixGateSemantic(np.eye(8, dtype=np.complex128)))

    def test_matrix_gate_semantic(self, gate: ThreeQubitGate) -> None:
        assert isinstance(gate.matrix, MatrixGateSemantic)

    def test_invalid_gate_semantic(self) -> None:
        gate = ThreeQubitGate(0, 1, 2, gate_semantic=CanonicalGateSemantic((0, 0, 0)))
        with pytest.raises(ValueError, match="invalid gate semantic"):
            _ = gate.matrix

    def test_is_identity(self) -> None:
        gate = ThreeQubitGate(0, 1, 2, gate_semantic=MatrixGateSemantic(np.eye(8, dtype=np.complex128)))
        assert gate.is_identity()

    def test_is_not_identity(self, gate: ThreeQubitGate) -> None:
        assert not gate.is_identity()


class TestDefaultThreeQubitGates:
    @pytest.mark.parametrize(
        ("gate", "expected_name"),
        [(CCX(0, 1, 2), "CCX"), (CSWAP(0, 1, 2), "CSWAP")],
        ids=["CCX", "CSWAP"],
    )
    def test_name(self, gate: ThreeQubitGate, expected_name: str) -> None:
        assert gate.name == expected_name

    def test_ccx_qubit_operands(self) -> None:
        gate = CCX(0, 1, 2)
        assert (gate.control_qubit_0, gate.control_qubit_1, gate.target_qubit) == (Qubit(0), Qubit(1), Qubit(2))

    def test_cswap_qubit_operands(self) -> None:
        gate = CSWAP(0, 1, 2)
        assert (gate.control_qubit, gate.qubit_0, gate.qubit_1) == (Qubit(0), Qubit(1), Qubit(2))

    def test_ccx_flips_target_when_both_controls_are_set(self) -> None:
        matrix = get_matrix(CCX(0, 1, 2), 3)
        # Basis states are indexed such that qubit i corresponds to bit i.
        for state in range(8):
            expected = state ^ 0b100 if state & 0b001 and state & 0b010 else state
            assert np.argmax(matrix[:, state]) == expected

    def test_cswap_swaps_targets_when_control_is_set(self) -> None:
        matrix = get_matrix(CSWAP(0, 1, 2), 3)
        for state in range(8):
            expected = state
            if state & 0b001:
                qubit_1, qubit_2 = (state >> 1) & 1, (state >> 2) & 1
                expected = (state & 0b001) | (qubit_2 << 1) | (qubit_1 << 2)
            assert np.argmax(matrix[:, state]) == expected

    @pytest.mark.parametrize(
        "gate",
        [CCX(0, 1, 2), CSWAP(0, 1, 2)],
        ids=["CCX", "CSWAP"],
    )
    def test_gate_is_unitary_and_self_inverse(self, gate: ThreeQubitGate) -> None:
        matrix = get_matrix(gate, 3)
        np.testing.assert_almost_equal(matrix @ matrix.conj().T, np.eye(8))
        np.testing.assert_almost_equal(matrix @ matrix, np.eye(8))

    def test_ccx_controls_are_interchangeable(self) -> None:
        assert CCX(0, 1, 2) == CCX(1, 0, 2)

    def test_ccx_target_is_not_interchangeable_with_a_control(self) -> None:
        assert CCX(0, 1, 2) != CCX(0, 2, 1)

    def test_cswap_targets_are_interchangeable(self) -> None:
        assert CSWAP(0, 1, 2) == CSWAP(0, 2, 1)
