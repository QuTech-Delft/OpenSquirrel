import math
from typing import List

import numpy as np
import pytest

from open_squirrel.circuit import Circuit
from open_squirrel.default_gates import Y90, X
from open_squirrel.register_manager import RegisterManager
from open_squirrel.reindexer.qubit_reindexer import get_reindexed_circuit
from open_squirrel.ir import BlochSphereRotation, ControlledGate, Gate, MatrixGate, Measure, Qubit, IR


class TestReindexer:
    @pytest.fixture
    def replacement_gates_2(self) -> List[Gate]:
        return [Y90(Qubit(1)), X(Qubit(3))]

    @pytest.fixture
    def replacement_gates_4(self) -> List[Gate]:
        return [
            Measure(Qubit(1)),
            BlochSphereRotation(Qubit(3), axis=(0, 0, 1), angle=math.pi),
            MatrixGate(
                np.array(
                    [
                        [1, 0, 0, 0],
                        [0, 0, 1, 0],
                        [0, 1, 0, 0],
                        [0, 0, 0, 1],
                    ]
                ),
                [Qubit(0), Qubit(3)],
            ),
            ControlledGate(Qubit(1), X(Qubit(2))),
        ]

    @pytest.fixture
    def circuit_3_reindexed(self) -> Circuit:
        ir = IR()
        ir.add_gate(Y90(Qubit(1)))
        ir.add_gate(X(Qubit(0)))
        return Circuit(RegisterManager(qubit_register_size=2), ir)

    @pytest.fixture
    def circuit_4_reindexed(self) -> Circuit:
        ir = IR()
        ir.add_gate(Measure(Qubit(0)))
        ir.add_gate(BlochSphereRotation(Qubit(2), axis=(0, 0, 1), angle=math.pi))
        ir.add_gate(
            MatrixGate(
                np.array(
                    [
                        [1, 0, 0, 0],
                        [0, 0, 1, 0],
                        [0, 1, 0, 0],
                        [0, 0, 0, 1],
                    ]
                ),
                [Qubit(1), Qubit(2)],
            )
        )
        ir.add_gate(ControlledGate(Qubit(0), X(Qubit(3))))
        return Circuit(RegisterManager(qubit_register_size=4), ir)

    @pytest.fixture
    def qubit_indices_2(self) -> List[int]:
        return [3, 1]

    @pytest.fixture
    def qubit_indices_4(self) -> List[int]:
        return [1, 0, 3, 2]

    def test_get_reindexed_circuit_3(
        self, replacement_gates_2: List[Gate], qubit_indices_2: List[int], circuit_3_reindexed: Circuit
    ) -> None:
        circuit_3 = get_reindexed_circuit(replacement_gates_2, qubit_indices_2)
        assert circuit_3 == circuit_3_reindexed

    def test_get_reindexed_circuit_4(
        self, replacement_gates_4: List[Gate], qubit_indices_4: List[int], circuit_4_reindexed: Circuit
    ) -> None:
        circuit_4 = get_reindexed_circuit(replacement_gates_4, qubit_indices_4)
        assert circuit_4 == circuit_4_reindexed
