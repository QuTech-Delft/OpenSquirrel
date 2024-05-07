from __future__ import annotations

from typing import List

import pytest

from opensquirrel import Circuit
from opensquirrel.default_gates import CNOT, H
from opensquirrel.mapper import HardcodedMapper, Mapper
from opensquirrel.mapper.mapping import Mapping
from opensquirrel.register_manager import RegisterManager
from opensquirrel.squirrel_ir import Comment, Measure, Qubit, SquirrelIR, Statement


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
        squirrel_ir = SquirrelIR()
        squirrel_ir.add_gate(H(Qubit(0)))
        squirrel_ir.add_gate(CNOT(Qubit(0), Qubit(1)))
        squirrel_ir.add_gate(CNOT(Qubit(1), Qubit(2)))
        squirrel_ir.add_comment(Comment("Qubit[1]"))
        squirrel_ir.add_measurement(Measure(Qubit(0), axis=(0, 0, 1)))
        return Circuit(register_manager, squirrel_ir)

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
        assert circuit.squirrel_ir.statements == expected_statements
