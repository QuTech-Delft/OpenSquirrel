from __future__ import annotations

import pytest

from opensquirrel import CircuitBuilder
from opensquirrel.decomposer import Decomposer
from opensquirrel.decomposer.general_decomposer import check_gate_replacement, decompose, replace
from opensquirrel.default_instructions import CNOT, Y90, H, I, X
from opensquirrel.ir import BlochSphereRotation, Gate


class TestCheckGateReplacement:
    @pytest.mark.parametrize(
        ("gate", "replacement_gates"),
        [
            (I(0), [I(0)]),
            (I(0), [I(0), I(0)]),
            (I(0), [H(0), H(0)]),
            (H(0), [H(0), H(0), H(0)]),
            (CNOT(0, 1), [CNOT(0, 1), I(0)]),
            # Arbitrary global phase change is not considered an issue.
            (CNOT(0, 1), [CNOT(0, 1), BlochSphereRotation(0, angle=0, axis=(1, 0, 0), phase=621.6546)]),
        ],
    )
    def test_valid_replacement(self, gate: Gate, replacement_gates: list[Gate]) -> None:
        check_gate_replacement(gate, replacement_gates)

    @pytest.mark.parametrize(
        ("gate", "replacement_gates", "error_msg"),
        [
            (H(0), [H(1)], "replacement for gate H does not seem to operate on the right qubits"),
            (CNOT(0, 1), [CNOT(2, 1)], "replacement for gate CNOT does not seem to operate on the right qubits"),
            (CNOT(0, 1), [CNOT(1, 0)], "replacement for gate CNOT does not preserve the quantum state"),
        ],
    )
    def test_wrong_qubit(self, gate: Gate, replacement_gates: list[Gate], error_msg: str) -> None:
        with pytest.raises(ValueError, match=error_msg):
            check_gate_replacement(gate, replacement_gates)

    def test_large_number_of_qubits(self) -> None:
        # If we were building the whole circuit matrix, this would run out of memory.
        check_gate_replacement(H(9234687), [Y90(9234687), X(9234687)])

        with pytest.raises(ValueError, match="replacement for gate H does not seem to operate on the right qubits"):
            check_gate_replacement(H(9234687), [Y90(698446519), X(9234687)])

        with pytest.raises(ValueError, match="replacement for gate H does not preserve the quantum state"):
            check_gate_replacement(H(9234687), [Y90(9234687), X(9234687), X(9234687)])


class TestReplacer:
    def test_replace_generic(self) -> None:
        builder1 = CircuitBuilder(3)
        builder1.H(0)
        builder1.CNOT(0, 1)
        circuit = builder1.to_circuit()

        # A simple decomposer function that adds identities before and after single-qubit gates.
        class TestDecomposer(Decomposer):
            def decompose(self, g: Gate) -> list[Gate]:
                if isinstance(g, BlochSphereRotation):
                    return [I(g.qubit), g, I(g.qubit)]
                return [g]

        decompose(circuit.ir, decomposer=TestDecomposer())

        builder2 = CircuitBuilder(3)
        builder2.I(0)
        builder2.H(0)
        builder2.I(0)
        builder2.CNOT(0, 1)
        expected_circuit = builder2.to_circuit()

        assert expected_circuit == circuit

    def test_replace(self) -> None:
        builder1 = CircuitBuilder(3)
        builder1.H(0)
        circuit = builder1.to_circuit()

        replace(circuit.ir, H, lambda q: [Y90(q), X(q)])

        builder2 = CircuitBuilder(3)
        builder2.Y90(0)
        builder2.X(0)
        expected_circuit = builder2.to_circuit()

        assert expected_circuit == circuit
