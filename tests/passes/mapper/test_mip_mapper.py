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
    expected_mapping = Mapping([4, 3, 2, 0, 1])
    mapping = mapper1.map(circuit1.ir, circuit1.qubit_register_size)
    assert mapping == expected_mapping


def test_mip_mapper_complex_connectivity(mapper2: MIPMapper, circuit2: Circuit) -> None:
    expected_mapping = Mapping([3, 4, 2, 5, 1, 0, 6])
    mapping = mapper2.map(circuit2.ir, circuit2.qubit_register_size)
    assert mapping == expected_mapping


def test_more_logical_qubits_than_physical(mapper1: MIPMapper, circuit3: Circuit) -> None:
    with pytest.raises(RuntimeError, match=r"Number of virtual qubits (.*) exceeds number of physical qubits (.*)"):
        mapper1.map(circuit3.ir, circuit3.qubit_register_size)


def test_timeout(mapper3: MIPMapper, circuit2: Circuit) -> None:
    with pytest.raises(RuntimeError, match="MIP solver failed"):
        # timeout used: 0.000001
        mapper3.map(circuit2.ir, circuit2.qubit_register_size)

def test_fewer_virtual_than_physical_qubits(mapper1: MIPMapper) -> None:
    """Test mapping a circuit with fewer virtual qubits than physical qubits available."""
    # mapper1 has connectivity with 5 physical qubits (0,1,2,3,4)
    # Create a circuit with only 3 virtual qubits
    builder = CircuitBuilder(3)
    builder.H(0)
    builder.CNOT(0, 1)
    builder.CNOT(1, 2)
    circuit = builder.to_circuit()
    
    # Should successfully map 3 virtual qubits to 5 physical qubits
    mapping = mapper1.map(circuit.ir, circuit.qubit_register_size)
    
    # Verify mapping properties
    assert len(mapping) == 3  # Should have exactly 3 mappings (one per virtual qubit)
    
    # Check that all physical qubits in the mapping are valid
    physical_qubits = [mapping[i] for i in range(3)]  # Get mapping for virtual qubits 0, 1, 2
    assert all(0 <= physical_qubit <= 4 for physical_qubit in physical_qubits)
    
    # All virtual qubits should map to different physical qubits
    assert len(set(physical_qubits)) == 3
