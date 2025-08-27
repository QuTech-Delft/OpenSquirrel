from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from opensquirrel import Circuit, CircuitBuilder
from opensquirrel.passes.mapper import HardcodedMapper
from opensquirrel.passes.mapper.general_mapper import Mapper
from opensquirrel.passes.mapper.mapping import Mapping

if TYPE_CHECKING:
    from opensquirrel.ir import IR


class TestMapper:
    def test_implementation(self) -> None:
        class Mapper2(Mapper):
            def __init__(self, qubit_register_size: int, **kwargs: Any) -> None:
                super().__init__(**kwargs)
                self._qubit_register = qubit_register_size

            def map(self, ir: IR, qubit_register_size: int) -> Mapping:
                return Mapping(list(range(self._qubit_register)))

        Mapper2(qubit_register_size=1)


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
