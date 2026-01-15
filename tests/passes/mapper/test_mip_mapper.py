# Tests for the MIPMapper pass

import pytest

from opensquirrel import CircuitBuilder
from opensquirrel.circuit import Circuit
from opensquirrel.passes.mapper import MIPMapper
from opensquirrel.passes.mapper.mapping import Mapping


@pytest.fixture
def mapper1() -> MIPMapper:
    connectivity = {"0": [1, 2], "1": [0, 2, 3], "2": [0, 1, 4], "3": [1, 4], "4": [2, 3]}

    return MIPMapper(connectivity=connectivity)


@pytest.fixture
def mapper2() -> MIPMapper:
    connectivity = {"0": [1, 2], "1": [0, 3], "2": [0, 4], "3": [1, 5], "4": [2, 5], "5": [3, 4, 6], "6": [5]}
    return MIPMapper(connectivity=connectivity)


@pytest.fixture
def mapper3() -> MIPMapper:
    connectivity = {"0": [2], "1": [0, 3, 4], "2": [0, 5], "3": [1, 5, 2], "4": [2, 5], "5": [4, 6], "6": [3]}
    timeout = 0.000001
    return MIPMapper(timeout=timeout, connectivity=connectivity)


@pytest.fixture
def mapper4() -> MIPMapper:
    connectivity = {"0": [1], "1": [0, 2], "2": [1, 3], "3": [2, 4], "4": [3]}
    return MIPMapper(connectivity=connectivity)


@pytest.fixture
def mapper5() -> MIPMapper:
    connectivity = {"0": [1], "1": [2, 0], "2": [1]}
    return MIPMapper(connectivity=connectivity)


@pytest.fixture
def circuit1() -> Circuit:
    builder = CircuitBuilder(5)
    builder.H(0)
    builder.CNOT(0, 1)
    builder.H(2)
    builder.CNOT(1, 2)
    builder.CNOT(2, 4)
    builder.CNOT(3, 4)
    return builder.to_circuit()


@pytest.fixture
def circuit2() -> Circuit:
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


@pytest.fixture
def circuit3() -> Circuit:
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
    expected_mapping = Mapping([0, 1, 2, 3, 4])
    mapping = mapper1.map(circuit1.ir, circuit1.qubit_register_size)
    assert mapping == expected_mapping


def test_mip_mapper_complex_connectivity(mapper2: MIPMapper, circuit2: Circuit) -> None:
    # expected_mapping = Mapping([3, 4, 2, 5, 1, 0, 6])
    expected_mapping = Mapping([2, 1, 3, 0, 4, 5, 6])
    mapping = mapper2.map(circuit2.ir, circuit2.qubit_register_size)
    assert mapping == expected_mapping


def test_more_logical_qubits_than_physical(mapper1: MIPMapper, circuit3: Circuit) -> None:
    with pytest.raises(RuntimeError, match=r"Number of virtual qubits (.*) exceeds number of physical qubits (.*)"):
        mapper1.map(circuit3.ir, circuit3.qubit_register_size)


def test_timeout(mapper3: MIPMapper, circuit2: Circuit) -> None:
    with pytest.raises(RuntimeError, match="MIP solver failed"):
        # timeout used: 0.000001
        mapper3.map(circuit2.ir, circuit2.qubit_register_size)


def test_map_method(mapper1: MIPMapper, circuit1: Circuit) -> None:
    initial_circuit = str(circuit1)
    circuit1.map(mapper=mapper1)
    assert str(circuit1) == initial_circuit


def test_fewer_virtual_than_physical_qubits(mapper1: MIPMapper) -> None:
    builder = CircuitBuilder(3)
    builder.H(0)
    builder.CNOT(0, 1)
    builder.CNOT(1, 2)
    circuit = builder.to_circuit()

    mapping = mapper1.map(circuit.ir, circuit.qubit_register_size)

    assert len(mapping) == 3

    physical_qubits = [mapping[i] for i in range(3)]
    assert all(0 <= physical_qubit <= 4 for physical_qubit in physical_qubits)

    assert len(set(physical_qubits)) == 3


def test_remap_controlled_gates(mapper4: MIPMapper, mapper5: MIPMapper) -> None:
    circuit = Circuit.from_string("""version 3.0; qubit[5] q; bit[2] b; H q[0]; CNOT q[0], q[1]; b = measure q[0, 1]""")

    circuit.map(mapper=mapper4)

    assert (
        str(circuit)
        == """version 3.0

qubit[5] q
bit[2] b

H q[0]
CNOT q[0], q[1]
b[0] = measure q[0]
b[1] = measure q[1]
"""
    )

    builder = CircuitBuilder(3)
    builder.CNOT(0, 1)
    builder.CNOT(0, 2)
    circuit = builder.to_circuit()

    circuit.map(mapper=mapper5)

    assert (
        str(circuit)
        == """version 3.0

qubit[3] q

CNOT q[1], q[0]
CNOT q[1], q[2]
"""
    )
