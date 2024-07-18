from __future__ import annotations

import pytest

from opensquirrel import Circuit, CircuitBuilder
from opensquirrel.default_gates import CNOT, H
from opensquirrel.ir import IR, Bit, Comment, Measure, Qubit, Statement
from opensquirrel.mapper import HardcodedMapper, Mapper
from opensquirrel.mapper.mapping import Mapping
from opensquirrel.register_manager import BitRegister, QubitRegister, RegisterManager


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
        circuit_builder = CircuitBuilder(3, 1)
        circuit_builder.H(Qubit(0))
        circuit_builder.CNOT(Qubit(0), Qubit(1))
        circuit_builder.CNOT(Qubit(1), Qubit(2))
        circuit_builder.comment("Qubit[1]")
        circuit_builder.measure(Qubit(0), Bit(0))
        return circuit_builder.to_circuit()

    @pytest.fixture(name="expected_statements")
    def expected_statements_fixture(self) -> list[Statement]:
        return [
            H(Qubit(1)),
            CNOT(Qubit(1), Qubit(0)),
            CNOT(Qubit(0), Qubit(2)),
            Comment("Qubit[1]"),
            Measure(Qubit(1), Bit(1), axis=(0, 0, 1)),
        ]

    def test_circuit_map(self, circuit: Circuit, expected_statements: list[Statement]) -> None:
        mapper = HardcodedMapper(circuit.qubit_register_size, Mapping([1, 0, 2]))
        circuit.map(mapper)
        assert circuit.ir.statements == expected_statements
