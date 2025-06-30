# Tests for the MIPMapper pass

import pytest

from opensquirrel import CircuitBuilder
from opensquirrel.circuit import Circuit
from opensquirrel.passes.mapper import MIPMapper
from opensquirrel.passes.mapper.mapping import Mapping


@pytest.fixture(name="mapper1")
def mapper_fixture1() -> MIPMapper:
    connectivity = {"0": [1, 2], "1": [0, 2, 3], "2": [0, 1, 4], "3": [1, 4], "4": [2, 3]}
    qubit_register_size = 5
    return MIPMapper(qubit_register_size=qubit_register_size, connectivity=connectivity)


@pytest.fixture(name="mapper2")
def mapper_fixture2() -> MIPMapper:
    connectivity = {"0": [1, 2], "1": [0, 3], "2": [0, 4], "3": [1, 5], "4": [2, 5], "5": [3, 4, 6], "6": [5]}
    qubit_register_size = 7
    return MIPMapper(qubit_register_size=qubit_register_size, connectivity=connectivity)


@pytest.fixture(name="mapper3")
def mapper_fixture3() -> MIPMapper:
    connectivity = {"0": [2], "1": [0, 3, 4], "2": [0, 5], "3": [1, 5, 2], "4": [2, 5], "5": [4, 6], "6": [3]}
    qubit_register_size = 7
    timeout = 0.000001
    return MIPMapper(qubit_register_size=qubit_register_size, timeout=timeout, connectivity=connectivity)


@pytest.fixture(name="circuit1")
def circuit_fixture1() -> Circuit:
    builder = CircuitBuilder(5)
    builder.H(0)
    builder.CNOT(0, 1)
    builder.H(2)
    builder.CNOT(1, 2)
    builder.CNOT(2, 4)
    builder.CNOT(3, 4)
    return builder.to_circuit()


@pytest.fixture(name="circuit2")
def circuit_fixture2() -> Circuit:
    builder = CircuitBuilder(7)
    builder.H(0)
    builder.CNOT(0, 1)
    builder.CNOT(0, 3)
    builder.H(2)
    builder.CNOT(1, 2)
    builder.CNOT(1, 3)
    builder.CNOT(2, 3)
    builder.CNOT(3, 4)
    builder.CNOT(0, 4)
    return builder.to_circuit()


@pytest.fixture(name="circuit3")
def circuit_fixture3() -> Circuit:
    builder = CircuitBuilder(7)
    builder.H(0)
    builder.CNOT(0, 1)
    builder.CNOT(0, 2)
    builder.CNOT(1, 3)
    builder.CNOT(2, 4)
    builder.CNOT(3, 5)
    builder.CNOT(4, 6)
    return builder.to_circuit()


def test_mip_mapper_simple_connectivity(mapper1: MIPMapper, circuit1: Circuit) -> None:
    expected_mapping = Mapping([4, 3, 2, 0, 1])
    mapping = mapper1.map(circuit1.ir)
    assert mapping == expected_mapping


def test_mip_mapper_complex_connectivity(mapper2: MIPMapper, circuit2: Circuit) -> None:
    expected_mapping = Mapping([3, 4, 2, 5, 1, 0, 6])
    mapping = mapper2.map(circuit2.ir)
    assert mapping == expected_mapping


def test_more_logical_qubits_than_physical(mapper1: MIPMapper, circuit3: Circuit) -> None:
    with pytest.raises(RuntimeError, match=r"Number of virtual qubits (.*) exceeds number of physical qubits (.*)"):
        mapper1.map(circuit3.ir)


def test_timeout(mapper3: MIPMapper, circuit2: Circuit) -> None:
    with pytest.raises(RuntimeError, match="MIP solver failed"):
        # timeout used: 0.000001
        mapper3.map(circuit2.ir)
