from __future__ import annotations

from typing import List

import pytest

from open_squirrel import Circuit
from open_squirrel.default_gates import CNOT, H
from open_squirrel.mapper import HardcodedMapper, Mapper
from open_squirrel.mapper.mapping import Mapping
from open_squirrel.register_manager import RegisterManager
from open_squirrel.ir import Comment, Measure, Qubit, IR, Statement


class TestMapper:
    def test_init(self) -> None:
        with pytest.raises(TypeError):
            Mapper()

    def test_implementation(self) -> None:
        class Mapper2(Mapper):
            pass

        with pytest.raises(TypeError):
            Mapper2()

        class Mapper3(Mapper2):
            def __init__(self, qubit_register_size: int) -> None:
                super().__init__(qubit_register_size, Mapping([0]))

        Mapper3(qubit_register_size=1)


class TestMapQubits:
    @pytest.fixture(name="circuit")
    def circuit_fixture(self) -> Circuit:
        register_manager = RegisterManager(qubit_register_size=3)
        ir = IR()
        ir.add_gate(H(Qubit(0)))
        ir.add_gate(CNOT(Qubit(0), Qubit(1)))
        ir.add_gate(CNOT(Qubit(1), Qubit(2)))
        ir.add_comment(Comment("Qubit[1]"))
        ir.add_measurement(Measure(Qubit(0), axis=(0, 0, 1)))
        return Circuit(register_manager, ir)

    @pytest.fixture(name="expected_statements")
    def expected_statements_fixture(self) -> List[Statement]:
        return [
            H(Qubit(1)),
            CNOT(Qubit(1), Qubit(0)),
            CNOT(Qubit(0), Qubit(2)),
            Comment("Qubit[1]"),
            Measure(Qubit(1), axis=(0, 0, 1)),
        ]

    def test_circuit_map(self, circuit: Circuit, expected_statements: list[Statement]) -> None:
        mapper = HardcodedMapper(circuit.qubit_register_size, Mapping([1, 0, 2]))
        circuit.map(mapper)
        assert circuit.ir.statements == expected_statements
