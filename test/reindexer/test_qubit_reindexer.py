from __future__ import annotations

import math

import numpy as np
import pytest

from opensquirrel.circuit import Circuit
from opensquirrel.default_gates import Y90, X
from opensquirrel.ir import IR, BlochSphereRotation, ControlledGate, Gate, MatrixGate, Measure, Qubit
from opensquirrel.register_manager import RegisterManager
from opensquirrel.reindexer.qubit_reindexer import get_reindexed_circuit


def circuit_1_reindexed() -> Circuit:
    ir = IR()
    ir.add_gate(Y90(Qubit(1)))
    ir.add_gate(X(Qubit(0)))
    return Circuit(RegisterManager(qubit_register_size=2), ir)


def replacement_gates_1() -> list[Gate]:
    return [Y90(Qubit(1)), X(Qubit(3))]


def replacement_gates_2() -> list[Gate]:
    return [
        Measure(Qubit(1)),
        BlochSphereRotation(Qubit(3), axis=(0, 0, 1), angle=math.pi),
        MatrixGate(np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]]), [Qubit(0), Qubit(3)]),
        ControlledGate(Qubit(1), X(Qubit(2))),
    ]


def circuit_2_reindexed() -> Circuit:
    ir = IR()
    ir.add_gate(Measure(Qubit(0)))
    ir.add_gate(BlochSphereRotation(Qubit(2), axis=(0, 0, 1), angle=math.pi))
    matrix = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]])
    ir.add_gate(MatrixGate(matrix, [Qubit(1), Qubit(2)]))
    ir.add_gate(ControlledGate(Qubit(0), X(Qubit(3))))
    return Circuit(RegisterManager(qubit_register_size=4), ir)


@pytest.mark.parametrize(
    "replacement_gates, qubit_indices, circuit_reindexed",
    [
        (replacement_gates_1(), [3, 1], circuit_1_reindexed()),
        (replacement_gates_2(), [1, 0, 3, 2], circuit_2_reindexed()),
    ],
    ids=["circuit1", "circuit2"],
)
def test_get_reindexed_circuit(
    replacement_gates: list[Gate], qubit_indices: list[int], circuit_reindexed: Circuit
) -> None:
    circuit = get_reindexed_circuit(replacement_gates, qubit_indices)
    assert circuit == circuit_reindexed
