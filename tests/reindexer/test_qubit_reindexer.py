from __future__ import annotations

from math import pi

import pytest

from opensquirrel import Y90, Circuit, CircuitBuilder, X
from opensquirrel.ir import Gate, Measure
from opensquirrel.ir.semantics import BlochSphereRotation, ControlledGateSemantic, MatrixGateSemantic
from opensquirrel.ir.single_qubit_gate import SingleQubitGate
from opensquirrel.ir.two_qubit_gate import TwoQubitGate
from opensquirrel.reindexer.qubit_reindexer import get_reindexed_circuit


def circuit_1_reindexed() -> Circuit:
    builder = CircuitBuilder(2)
    builder.Y90(1)
    builder.X(0)
    return builder.to_circuit()


def replacement_gates_1() -> list[Gate]:
    return [Y90(1), X(3)]


def replacement_gates_2() -> list[Gate | Measure]:
    return [
        Measure(1, 1),
        SingleQubitGate(qubit=3, gate_semantic=BlochSphereRotation(axis=(0, 0, 1), angle=pi, phase=pi / 2)),
        TwoQubitGate(
            qubit0=0,
            qubit1=3,
            gate_semantic=MatrixGateSemantic([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]]),
        ),
        TwoQubitGate(qubit0=1, qubit1=2, gate_semantic=ControlledGateSemantic(target_gate=X(2))),
    ]


def circuit_2_reindexed() -> Circuit:
    builder = CircuitBuilder(4, 4)
    builder.measure(0, 0)
    builder.ir.add_gate(
        SingleQubitGate(qubit=2, gate_semantic=BlochSphereRotation(axis=(0, 0, 1), angle=pi, phase=pi / 2))
    )
    builder.ir.add_gate(
        TwoQubitGate(1, 2, gate_semantic=MatrixGateSemantic([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]]))
    )
    builder.ir.add_gate(TwoQubitGate(0, 3, gate_semantic=ControlledGateSemantic(target_gate=X(3))))
    return builder.to_circuit()


@pytest.mark.parametrize(
    ("replacement_gates", "qubit_indices", "bit_register_size", "circuit_reindexed"),
    [
        (replacement_gates_1(), [3, 1], 0, circuit_1_reindexed()),
        (replacement_gates_2(), [1, 0, 3, 2], 4, circuit_2_reindexed()),
    ],
    ids=["circuit1", "circuit2"],
)
def test_get_reindexed_circuit(
    replacement_gates: list[Gate],
    qubit_indices: list[int],
    bit_register_size: int,
    circuit_reindexed: Circuit,
) -> None:
    circuit = get_reindexed_circuit(replacement_gates, qubit_indices, bit_register_size)
    assert circuit == circuit_reindexed
