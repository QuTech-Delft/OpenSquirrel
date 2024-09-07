from __future__ import annotations

import math

import pytest

from opensquirrel import CircuitBuilder
from opensquirrel.decomposer.general_decomposer import Decomposer, check_gate_replacement, decompose, replace
from opensquirrel.decomposer.twoqubitgate_decomposer import TwoQubitGateFolder
from opensquirrel.default_gates import CNOT, Y90, H, I, Ry, Rz, X, Z, sqrtSWAP
from opensquirrel.ir import BlochSphereRotation, Float, Gate, Qubit

class TestCheckTwoQubitDecomposer:
    """check if HZH gate can be folded to X
    H(Qubit(0)),Z(Qubit(0)),H(Qubit(0))) -> X(Qubit(0)))
    """
    def test_HZH_to_X(self):
        builder1 = CircuitBuilder(3)
        builder1.H(Qubit(0))
        builder1.Z(Qubit(0))
        builder1.H(Qubit(0))
        circuit = builder1.to_circuit()
        decompose(circuit.ir,decomposer=TwoQubitGateFolder())
        assert(len(circuit.ir.statements) == 1)

class TestCheckGateReplacement:
    @pytest.mark.parametrize(
        ("gate", "replacement_gates"),
        [
            (I(Qubit(0)), [I(Qubit(0))]),
            (I(Qubit(0)), [I(Qubit(0)), I(Qubit(0))]),
            (I(Qubit(0)), [H(Qubit(0)), H(Qubit(0))]),
            (H(Qubit(0)), [H(Qubit(0)), H(Qubit(0)), H(Qubit(0))]),
            (CNOT(Qubit(0), Qubit(1)), [CNOT(Qubit(0), Qubit(1)), I(Qubit(0))]),
            # Arbitrary global phase change is not considered an issue.
            (
                CNOT(Qubit(0), Qubit(1)),
                [CNOT(Qubit(0), Qubit(1)), BlochSphereRotation(Qubit(0), angle=0, axis=(1, 0, 0), phase=621.6546)],
            ),
        ],
    )
    def test_valid_replacement(self, gate: Gate, replacement_gates: list[Gate]) -> None:
        check_gate_replacement(gate, replacement_gates)

    @pytest.mark.parametrize(
        ("gate", "replacement_gates", "error_msg"),
        [
            (H(Qubit(0)), [H(Qubit(1))], "replacement for gate H does not seem to operate on the right qubits"),
            (
                CNOT(Qubit(0), Qubit(1)),
                [CNOT(Qubit(2), Qubit(1))],
                "replacement for gate CNOT does not seem to operate on the right qubits",
            ),
            (
                CNOT(Qubit(0), Qubit(1)),
                [CNOT(Qubit(1), Qubit(0))],
                "replacement for gate CNOT does not preserve the quantum state",
            ),
        ],
    )
    def test_wrong_qubit(self, gate: Gate, replacement_gates: list[Gate], error_msg: str) -> None:
        with pytest.raises(ValueError, match=error_msg):
            check_gate_replacement(gate, replacement_gates)

    def test_cnot_as_sqrt_swap(self) -> None:
        # https://en.wikipedia.org/wiki/Quantum_logic_gate#/media/File:Qcircuit_CNOTsqrtSWAP2.svg
        c = Qubit(0)
        t = Qubit(1)
        check_gate_replacement(
            CNOT(control=c, target=t),
            [
                Ry(t, Float(math.pi / 2)),
                sqrtSWAP(c, t),
                Z(c),
                sqrtSWAP(c, t),
                Rz(c, Float(-math.pi / 2)),
                Rz(t, Float(-math.pi / 2)),
                Ry(t, Float(-math.pi / 2)),
            ],
        )

        with pytest.raises(ValueError, match="replacement for gate CNOT does not preserve the quantum state"):
            check_gate_replacement(
                CNOT(control=c, target=t),
                [
                    Ry(t, Float(math.pi / 2)),
                    sqrtSWAP(c, t),
                    Z(c),
                    sqrtSWAP(c, t),
                    Rz(c, Float(-math.pi / 2 + 0.01)),
                    Rz(t, Float(-math.pi / 2)),
                    Ry(t, Float(-math.pi / 2)),
                ],
            )

        with pytest.raises(ValueError, match="replacement for gate CNOT does not seem to operate on the right qubits"):
            check_gate_replacement(
                CNOT(control=c, target=t),
                [
                    Ry(t, Float(math.pi / 2)),
                    sqrtSWAP(c, t),
                    Z(c),
                    sqrtSWAP(c, Qubit(2)),
                    Rz(c, Float(-math.pi / 2 + 0.01)),
                    Rz(t, Float(-math.pi / 2)),
                    Ry(t, Float(-math.pi / 2)),
                ],
            )

    def test_large_number_of_qubits(self) -> None:
        # If we were building the whole circuit matrix, this would run out of memory.
        check_gate_replacement(H(Qubit(9234687)), [Y90(Qubit(9234687)), X(Qubit(9234687))])

        with pytest.raises(ValueError, match="replacement for gate H does not seem to operate on the right qubits"):
            check_gate_replacement(H(Qubit(9234687)), [Y90(Qubit(698446519)), X(Qubit(9234687))])

        with pytest.raises(ValueError, match="replacement for gate H does not preserve the quantum state"):
            check_gate_replacement(H(Qubit(9234687)), [Y90(Qubit(9234687)), X(Qubit(9234687)), X(Qubit(9234687))])


class TestReplacer:
    def test_replace_generic(self) -> None:
        builder1 = CircuitBuilder(3)
        builder1.H(Qubit(0))
        builder1.CNOT(Qubit(0), Qubit(1))
        circuit = builder1.to_circuit()

        # A simple decomposer function that adds identities before and after single-qubit gates.
        class TestDecomposer(Decomposer):
            def decompose(self, g: Gate,gates_before : list[Statement] = [], gates_after : list[Statement] = []) -> list[Gate]:
                if isinstance(g, BlochSphereRotation):
                    return [I(g.qubit), g, I(g.qubit)]
                return [g]

        decompose(circuit.ir, decomposer=TestDecomposer())

        builder2 = CircuitBuilder(3)
        builder2.I(Qubit(0))
        builder2.H(Qubit(0))
        builder2.I(Qubit(0))
        builder2.CNOT(Qubit(0), Qubit(1))
        expected_circuit = builder2.to_circuit()

        assert expected_circuit == circuit

    def test_replace(self) -> None:
        builder1 = CircuitBuilder(3)
        builder1.H(Qubit(0))
        builder1.comment("Test comment.")
        circuit = builder1.to_circuit()

        replace(circuit.ir, H, lambda q: [Y90(q), X(q)])

        builder2 = CircuitBuilder(3)
        builder2.Y90(Qubit(0))
        builder2.X(Qubit(0))
        builder2.comment("Test comment.")
        expected_circuit = builder2.to_circuit()

        assert expected_circuit == circuit
