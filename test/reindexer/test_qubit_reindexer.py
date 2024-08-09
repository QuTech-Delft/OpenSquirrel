from __future__ import annotations

import math

import numpy as np
import pytest

from opensquirrel import Circuit, CircuitBuilder
from opensquirrel.default_gates import Y90, X
from opensquirrel.ir import (Bit, BlochSphereRotation, ControlledGate, Gate,
                             MatrixGate, Measure, Qubit)
from opensquirrel.reindexer.qubit_reindexer import get_reindexed_circuit


def circuit_1_reindexed() -> Circuit:
    builder = CircuitBuilder(2)
    builder.Y90(Qubit(1))
    builder.X(Qubit(0))
    return builder.to_circuit()


def replacement_gates_1() -> list[Gate]:
    return [Y90(Qubit(1)), X(Qubit(3))]


def replacement_gates_2() -> list[Gate]:
    return [
        Measure(Qubit(1), Bit(1)),
        BlochSphereRotation(Qubit(3), axis=(0, 0, 1), angle=math.pi),
        MatrixGate(np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]]), [Qubit(0), Qubit(3)]),
        ControlledGate(Qubit(1), X(Qubit(2))),
    ]


def circuit_2_reindexed() -> Circuit:
    builder = CircuitBuilder(4, 4)
    builder.measure(Qubit(0), Bit(0))
    builder.ir.add_gate(BlochSphereRotation(Qubit(2), axis=(0, 0, 1), angle=math.pi))
    matrix = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]])
    builder.ir.add_gate(MatrixGate(matrix, [Qubit(1), Qubit(2)]))
    builder.ir.add_gate(ControlledGate(Qubit(0), X(Qubit(3))))
    return builder.to_circuit()


@pytest.mark.parametrize(
    "replacement_gates, qubit_indices, bit_register_size, circuit_reindexed",
    [
        (replacement_gates_1(), [3, 1], 0, circuit_1_reindexed()),
        (replacement_gates_2(), [1, 0, 3, 2], 4, circuit_2_reindexed()),
    ],
    ids=["circuit1", "circuit2"],
)
def test_get_reindexed_circuit(
    replacement_gates: list[Gate], qubit_indices: list[int], bit_register_size: int, circuit_reindexed: Circuit
) -> None:
    circuit = get_reindexed_circuit(replacement_gates, qubit_indices, bit_register_size)
    assert circuit == circuit_reindexed
