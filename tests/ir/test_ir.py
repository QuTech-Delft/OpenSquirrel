from math import pi

import numpy as np
import pytest

from opensquirrel.ir import (
    IR,
    AsmDeclaration,
    Barrier,
    Bit,
    Init,
    IRVisitor,
    Measure,
    Qubit,
)
from opensquirrel.ir.semantics import BlochSphereRotation, ControlledGateSemantic, MatrixGateSemantic
from opensquirrel.ir.single_qubit_gate import SingleQubitGate
from opensquirrel.ir.two_qubit_gate import TwoQubitGate


class TestIR:
    def test_cnot_equality(self) -> None:
        matrix = np.array(
            [
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 0, 1],
                [0, 0, 1, 0],
            ],
        )
        cnot_matrix_gate = TwoQubitGate(qubit0=4, qubit1=100, gate_semantic=MatrixGateSemantic(matrix))

        cnot_controlled_gate = TwoQubitGate(
            qubit0=4,
            qubit1=100,
            gate_semantic=ControlledGateSemantic(BlochSphereRotation(axis=(1, 0, 0), angle=pi, phase=pi / 2)),
        )

        assert cnot_controlled_gate == cnot_matrix_gate

    def test_different_qubits_gate(self) -> None:
        matrix = [
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
        ]
        large_identity_matrix_gate = TwoQubitGate(qubit0=0, qubit1=2, gate_semantic=MatrixGateSemantic(matrix))

        small_identity_control_gate = TwoQubitGate(
            qubit0=0,
            qubit1=2,
            gate_semantic=ControlledGateSemantic(BlochSphereRotation(axis=(1, 0, 0), angle=0, phase=0)),
        )

        assert large_identity_matrix_gate == small_identity_control_gate

    def test_inverse_gate(self) -> None:
        matrix = [
            [1, 0, 0, 0],
            [0, 0, 0, 1],
            [0, 0, 1, 0],
            [0, 1, 0, 0],
        ]
        inverted_matrix_gate = TwoQubitGate(qubit0=0, qubit1=1, gate_semantic=MatrixGateSemantic(matrix))

        inverted_cnot_gate = TwoQubitGate(
            qubit0=1,
            qubit1=0,
            gate_semantic=ControlledGateSemantic(BlochSphereRotation(axis=(1, 0, 0), angle=pi, phase=pi / 2)),
        )

        assert inverted_matrix_gate == inverted_cnot_gate

    def test_global_phase(self) -> None:
        matrix = [
            [1j, 0, 0, 0],
            [0, 0, 0, 1j],
            [0, 0, 1j, 0],
            [0, 1j, 0, 0],
        ]
        inverted_matrix_with_phase = TwoQubitGate(qubit0=0, qubit1=1, gate_semantic=MatrixGateSemantic(matrix))

        inverted_cnot_gate = TwoQubitGate(
            qubit0=1,
            qubit1=0,
            gate_semantic=ControlledGateSemantic(BlochSphereRotation(axis=(1, 0, 0), angle=pi, phase=pi / 2)),
        )

        assert inverted_matrix_with_phase == inverted_cnot_gate

    def test_cnot_inequality(self) -> None:
        matrix = [
            [1, 0, 0, 0],
            [0, 0, 1, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1],
        ]
        swap_matrix_gate = TwoQubitGate(qubit0=4, qubit1=100, gate_semantic=MatrixGateSemantic(matrix))

        cnot_controlled_gate = TwoQubitGate(
            qubit0=4,
            qubit1=100,
            gate_semantic=ControlledGateSemantic(BlochSphereRotation(axis=(1, 0, 0), angle=pi, phase=pi / 2)),
        )

        assert cnot_controlled_gate != swap_matrix_gate

    def test_hash_difference_bit_qubit(self) -> None:
        assert hash(Qubit(1)) != hash(Bit(1))

    def test_repr(self) -> None:
        ir = IR()
        assert repr(ir) == "IR: []"

        ir.add_statement(Init(0))
        ir.add_statement(Barrier(0))
        ir.add_statement(Measure(0, 0))
        ir.add_statement(SingleQubitGate(0, BlochSphereRotation(axis=(1, 0, 0), angle=pi, phase=pi / 2)))
        ir.add_statement(AsmDeclaration("TestBackend", "some backend code"))
        assert repr(ir) == (
            "IR: [Init(qubit=Qubit[0]), Barrier(qubit=Qubit[0]), "
            "Measure(qubit=Qubit[0], bit=Bit[0], axis=Axis[0. 0. 1.]), "
            "SingleQubitGate(qubit=Qubit[0], "
            "gate_semantic=BlochSphereRotation(axis=[1. 0. 0.], angle=3.14159, phase=1.5708)), "
            "AsmDeclaration(backend_name=TestBackend)]"
        )


class TestIRVisitor:
    @pytest.mark.parametrize("method_name", [name for name in dir(IRVisitor) if name.startswith("visit_")])
    def test_default_returns_none(self, method_name: str) -> None:
        assert getattr(IRVisitor(), method_name)(None) is None
