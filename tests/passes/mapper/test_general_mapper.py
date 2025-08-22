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
        class IncompleteMapper(Mapper):
            pass

        incomplete_mapper = IncompleteMapper()

        builder = CircuitBuilder(1)
        builder.H(0)
        circuit = builder.to_circuit()

        with pytest.raises(NotImplementedError):
            incomplete_mapper.map(circuit.ir, circuit.qubit_register_size)

        class ProperMapper(Mapper):
            def map(self, ir: IR, qubit_register_size: int) -> Mapping:
                return Mapping(list(range(qubit_register_size)))

        proper_mapper = ProperMapper()
        mapping = proper_mapper.map(circuit.ir, circuit.qubit_register_size)
        assert len(mapping) == circuit.qubit_register_size


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
