# Tests for the simple mapper passes
from __future__ import annotations

import random

import pytest

from opensquirrel import Circuit, CircuitBuilder
from opensquirrel.passes.mapper import HardcodedMapper, IdentityMapper, RandomMapper
from opensquirrel.passes.mapper.mapping import Mapping
from opensquirrel.utils import check_mapper


class TestIdentityMapper:
    @pytest.fixture
    def mapper(self) -> IdentityMapper:
        return IdentityMapper()

    @pytest.fixture
    def circuit(self) -> Circuit:
        builder = CircuitBuilder(3)
        builder.H(0)
        return builder.to_circuit()

    def test_compliance(self, mapper: IdentityMapper) -> None:
        check_mapper(mapper)

    def test_get_mapping(self, mapper: IdentityMapper, circuit: Circuit) -> None:
        mapping = mapper.map(circuit.ir, circuit.qubit_register_size)
        assert mapping == Mapping([0, 1, 2])


class TestHardcodedMapper:
    @pytest.fixture
    def mapper(self) -> HardcodedMapper:
        mapping = Mapping([1, 2, 3, 4, 5, 6, 7, 8, 9, 0])
        return HardcodedMapper(mapping=mapping)

    @pytest.fixture
    def circuit(self) -> Circuit:
        builder = CircuitBuilder(10)
        builder.H(0)
        return builder.to_circuit()

    def test_compliance(self, mapper: HardcodedMapper) -> None:
        check_mapper(mapper)

    def test_get_mapping(self, mapper: HardcodedMapper, circuit: Circuit) -> None:
        mapping = mapper.map(circuit.ir, circuit.qubit_register_size)
        assert mapping == Mapping([1, 2, 3, 4, 5, 6, 7, 8, 9, 0])


class TestRandomMapper:
    @pytest.fixture
    def mapper(self) -> RandomMapper:
        return RandomMapper()

    @pytest.fixture
    def circuit(self) -> Circuit:
        builder = CircuitBuilder(5)
        builder.H(0)
        return builder.to_circuit()

    def test_compliance(self, mapper: RandomMapper) -> None:
        check_mapper(mapper)

    def test_get_mapping(self, mapper: RandomMapper, circuit: Circuit) -> None:
        mapping = mapper.map(circuit.ir, circuit.qubit_register_size)
        assert len(mapping) == 5

    @pytest.mark.parametrize("seed, qubit_register_size", [(42, 5), (123, 10), (456, 20)])  # noqa: PT006
    def test_mapping_uniqueness(self, seed: int, qubit_register_size: int) -> None:
        random.seed(seed)
        mapper = RandomMapper(seed=seed)

        builder = CircuitBuilder(qubit_register_size)
        builder.H(0)
        circuit = builder.to_circuit()

        original_mapping = Mapping(list(range(qubit_register_size)))
        new_mapping = mapper.map(circuit.ir, circuit.qubit_register_size)

        assert new_mapping != original_mapping
