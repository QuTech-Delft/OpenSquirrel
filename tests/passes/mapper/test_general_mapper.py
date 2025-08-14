from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from opensquirrel import Circuit, CircuitBuilder
from opensquirrel.passes.mapper import HardcodedMapper
from opensquirrel.passes.mapper.general_mapper import Mapper
from opensquirrel.passes.mapper.mapping import Mapping

if TYPE_CHECKING:
    from opensquirrel.ir import IR


class TestMapper:
    def test_init(self) -> None:
        mapper = Mapper()
        assert mapper is not None

    def test_implementation(self) -> None:
        class Mapper2(Mapper):
            pass

        mapper2 = Mapper2()
        assert mapper2 is not None

        builder = CircuitBuilder(1)
        builder.H(0)
        circuit = builder.to_circuit()

        with pytest.raises(NotImplementedError):
            mapper2.map(circuit.ir, circuit.qubit_register_size)

        class Mapper3(Mapper2):
            def map(self, ir: IR, qubit_register_size: int) -> Mapping:
                return Mapping([0])

        mapper3 = Mapper3()
        mapping = mapper3.map(circuit.ir, circuit.qubit_register_size)
        assert mapping == Mapping([0])


class TestMapQubits:
    @pytest.fixture
    def circuit(self) -> Circuit:
        builder = CircuitBuilder(3, 1)
        builder.H(0)
        builder.CNOT(0, 1)
        builder.CNOT(1, 2)
        builder.measure(0, 0)
        return builder.to_circuit()

    @pytest.fixture
    def remapped_circuit(self) -> Circuit:
        builder = CircuitBuilder(3, 1)
        builder.H(1)
        builder.CNOT(1, 0)
        builder.CNOT(0, 2)
        builder.measure(1, 0)
        return builder.to_circuit()

    def test_circuit_map(self, circuit: Circuit, remapped_circuit: Circuit) -> None:
        mapper = HardcodedMapper(mapping=Mapping([1, 0, 2]))
        circuit.map(mapper=mapper)
        assert circuit == remapped_circuit
