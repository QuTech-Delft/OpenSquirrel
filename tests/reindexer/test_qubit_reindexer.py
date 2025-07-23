from __future__ import annotations

import math

import pytest

from opensquirrel import Y90, Circuit, CircuitBuilder, X
from opensquirrel.ir import BlochSphereRotation, ControlledGate, Gate, MatrixGate, Measure
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
        BlochSphereRotation(3, axis=(0, 0, 1), angle=math.pi, phase=math.pi / 2),
        MatrixGate([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], [0, 3]),
        ControlledGate(1, X(2)),
    ]


def circuit_2_reindexed() -> Circuit:
    builder = CircuitBuilder(4, 4)
    builder.measure(0, 0)
    builder.ir.add_gate(BlochSphereRotation(2, axis=(0, 0, 1), angle=math.pi, phase=math.pi / 2))
    builder.ir.add_gate(MatrixGate([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], [1, 2]))
    builder.ir.add_gate(ControlledGate(0, X(3)))
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
