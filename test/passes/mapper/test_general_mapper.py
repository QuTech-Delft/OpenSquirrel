from __future__ import annotations

import pytest

from opensquirrel import Circuit, CircuitBuilder
from opensquirrel.passes.mapper import HardcodedMapper, Mapper
from opensquirrel.passes.mapper.mapping import Mapping


class TestMapper:
    def test_init(self) -> None:
        with pytest.raises(TypeError):
            Mapper()  # type: ignore[call-arg]

    def test_implementation(self) -> None:
        class Mapper2(Mapper):
            pass

        with pytest.raises(TypeError):
            Mapper2()  # type: ignore[call-arg]

        class Mapper3(Mapper2):
            def __init__(self, qubit_register_size: int) -> None:
                super().__init__(qubit_register_size, Mapping([0]))

        Mapper3(qubit_register_size=1)


class TestMapQubits:
    @pytest.fixture(name="circuit")
    def circuit_fixture(self) -> Circuit:
        builder = CircuitBuilder(3, 1)
        builder.H(0)
        builder.CNOT(0, 1)
        builder.CNOT(1, 2)
        builder.measure(0, 0)
        return builder.to_circuit()

    @pytest.fixture(name="remapped_circuit")
    def remapped_circuit_fixture(self) -> Circuit:
        builder = CircuitBuilder(3, 1)
        builder.H(1)
        builder.CNOT(1, 0)
        builder.CNOT(0, 2)
        builder.measure(1, 0)
        return builder.to_circuit()

    def test_circuit_map(self, circuit: Circuit, remapped_circuit: Circuit) -> None:
        mapper = HardcodedMapper(circuit.qubit_register_size, Mapping([1, 0, 2]))
        circuit.map(mapper)
        assert circuit == remapped_circuit
