from __future__ import annotations

import pytest

from opensquirrel import Circuit, CircuitBuilder
from opensquirrel.ir import Bit, Qubit
from opensquirrel.mapper import HardcodedMapper, Mapper
from opensquirrel.mapper.mapping import Mapping


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

    @pytest.fixture(name="remapped_circuit")
    def remapped_circuit_fixture(self) -> Circuit:
        circuit_builder = CircuitBuilder(3, 1)
        circuit_builder.H(Qubit(1))
        circuit_builder.CNOT(Qubit(1), Qubit(0))
        circuit_builder.CNOT(Qubit(0), Qubit(2))
        circuit_builder.comment("Qubit[1]")
        circuit_builder.measure(Qubit(1), Bit(0))
        return circuit_builder.to_circuit()

    def test_circuit_map(self, circuit: Circuit, remapped_circuit: Circuit) -> None:
        mapper = HardcodedMapper(circuit.qubit_register_size, Mapping([1, 0, 2]))
        circuit.map(mapper)
        assert circuit == remapped_circuit
