from __future__ import annotations

import math

import pytest

from opensquirrel.circuit import Circuit
from opensquirrel.decomposer import general_decomposer
from opensquirrel.decomposer.general_decomposer import Decomposer, check_gate_replacement
from opensquirrel.default_gates import CNOT, Y90, BlochSphereRotation, H, I, Ry, Rz, X, Z, sqrtSWAP
from opensquirrel.ir import IR, Comment, Float, Gate, Qubit
from opensquirrel.register_manager import QubitRegister, RegisterManager


class TestCheckGateReplacement:

    @pytest.mark.parametrize(
        "gate, replacement_gates",
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
        "gate, replacement_gates, error_msg",
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

    def test_cnot_as_sqrt_swap(self):
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

    def test_large_number_of_qubits(self):
        # If we were building the whole circuit matrix, this would run out of memory.
        check_gate_replacement(H(Qubit(9234687)), [Y90(Qubit(9234687)), X(Qubit(9234687))])

        with pytest.raises(ValueError, match="replacement for gate H does not seem to operate on the right qubits"):
            check_gate_replacement(H(Qubit(9234687)), [Y90(Qubit(698446519)), X(Qubit(9234687))])

        with pytest.raises(ValueError, match="replacement for gate H does not preserve the quantum state"):
            check_gate_replacement(H(Qubit(9234687)), [Y90(Qubit(9234687)), X(Qubit(9234687)), X(Qubit(9234687))])


class TestReplacer:
    def test_replace_generic(self):
        register_manager = RegisterManager(QubitRegister(3))
        ir = IR()
        ir.add_gate(H(Qubit(0)))
        ir.add_gate(CNOT(Qubit(0), Qubit(1)))
        circuit = Circuit(register_manager, ir)

        # A simple decomposer function that adds identities before and after single-qubit gates.
        class TestDecomposer(Decomposer):
            def decompose(self, g: Gate) -> list[Gate]:
                if isinstance(g, BlochSphereRotation):
                    return [BlochSphereRotation.identity(g.qubit), g, BlochSphereRotation.identity(g.qubit)]
                return [g]

        general_decomposer.decompose(ir, decomposer=TestDecomposer())

        expected_ir = IR()
        expected_ir.add_gate(BlochSphereRotation.identity(Qubit(0)))
        expected_ir.add_gate(H(Qubit(0)))
        expected_ir.add_gate(BlochSphereRotation.identity(Qubit(0)))
        expected_ir.add_gate(CNOT(Qubit(0), Qubit(1)))
        expected_circuit = Circuit(register_manager, expected_ir)

        assert expected_circuit == circuit

    def test_replace(self):
        register_manager = RegisterManager(QubitRegister(3))
        ir = IR()
        ir.add_gate(H(Qubit(0)))
        ir.add_comment(Comment("Test comment."))
        circuit = Circuit(register_manager, ir)

        general_decomposer.replace(ir, H, lambda q: [Y90(q), X(q)])

        expected_ir = IR()
        expected_ir.add_gate(Y90(Qubit(0)))
        expected_ir.add_gate(X(Qubit(0)))
        expected_ir.add_comment(Comment("Test comment."))
        expected_circuit = Circuit(register_manager, expected_ir)

        assert expected_circuit == circuit
