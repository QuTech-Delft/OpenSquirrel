from typing import List

import pytest

from opensquirrel.circuit import Circuit
from opensquirrel.default_gates import Y90, X
from opensquirrel.register_manager import RegisterManager
from opensquirrel.reindexer.qubit_reindexer import get_reindexed_circuit
from opensquirrel.squirrel_ir import Gate, Qubit, SquirrelIR


class TestReindexer:
    @pytest.fixture
    def replacement_gates_2(self) -> List[Gate]:
        return [Y90(Qubit(1)), X(Qubit(3))]

    @pytest.fixture
    def replacement_gates_4(self) -> List[Gate]:
        return [Y90(Qubit(1)), X(Qubit(3)), Y90(Qubit(0)), X(Qubit(2))]

    @pytest.fixture
    def circuit_3_reindexed(self) -> Circuit:
        squirrel_ir = SquirrelIR()
        squirrel_ir.add_gate(Y90(Qubit(1)))
        squirrel_ir.add_gate(X(Qubit(0)))
        return Circuit(RegisterManager(qubit_register_size=2), squirrel_ir)

    @pytest.fixture
    def circuit_4_reindexed(self) -> Circuit:
        squirrel_ir = SquirrelIR()
        squirrel_ir.add_gate(Y90(Qubit(0)))
        squirrel_ir.add_gate(X(Qubit(2)))
        squirrel_ir.add_gate(Y90(Qubit(1)))
        squirrel_ir.add_gate(X(Qubit(3)))
        return Circuit(RegisterManager(qubit_register_size=4), squirrel_ir)

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
