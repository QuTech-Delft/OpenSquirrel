# Tests for the QGymMapper class
import json
from importlib.resources import files

import networkx as nx
import pytest

from opensquirrel import CircuitBuilder
from opensquirrel.circuit import Circuit
from opensquirrel.passes.mapper import QGymMapper
from opensquirrel.passes.mapper.mapping import Mapping

CONNECTIVITY_SCHEMES = json.loads(
    (files("opensquirrel.passes.mapper") / "connectivities.json").read_text(encoding="utf-8")
)
AGENT1 = "opensquirrel/passes/mapper/TRPO_tuna5_2e5.zip"
AGENT2 = "opensquirrel/passes/mapper/TRPO_starmon7_5e5.zip"
AGENT_CLASS = "TRPO"


@pytest.fixture
def mapper1() -> QGymMapper:
    agent_class = AGENT_CLASS
    agent_path = AGENT1
    connectivity = CONNECTIVITY_SCHEMES["tuna-5"]
    connection_graph = nx.Graph()
    connection_graph.add_edges_from(connectivity)
    return QGymMapper(agent_class, agent_path, connection_graph)


@pytest.fixture
def mapper2() -> QGymMapper:
    agent_class = AGENT_CLASS
    agent_path = AGENT2
    connectivity = CONNECTIVITY_SCHEMES["starmon-7"]
    connection_graph = nx.Graph()
    connection_graph.add_edges_from(connectivity)
    return QGymMapper(agent_class, agent_path, connection_graph)


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
    builder.CNOT(0, 6)
    builder.H(2)
    builder.CNOT(1, 5)
    builder.CNOT(2, 4)
    builder.CNOT(3, 6)
    builder.H(5)
    builder.CNOT(0, 2)
    builder.CNOT(1, 3)
    builder.CNOT(4, 5)
    builder.CNOT(5, 6)
    return builder.to_circuit()


@pytest.mark.parametrize(
    "mapper, circuit, expected_mapping_length",  # noqa: PT006
    [("mapper1", "circuit1", 5), ("mapper2", "circuit2", 7)],
)
def test_mapping(
    mapper: QGymMapper, circuit: Circuit, expected_mapping_length: int, request: pytest.FixtureRequest
) -> None:
    circuit = request.getfixturevalue(circuit)  # type: ignore[arg-type]
    mapper = request.getfixturevalue(mapper)  # type: ignore[arg-type]
    mapping = mapper.map(circuit.ir, circuit.qubit_register_size)
    assert isinstance(mapping, Mapping)
    assert len(mapping) == expected_mapping_length


def test_map_on_circuit(mapper1: QGymMapper, circuit1: Circuit) -> None:
    initial_circuit = str(circuit1)
    circuit1.map(mapper=mapper1)
    assert str(circuit1) != initial_circuit


def test_check_not_many_logical_as_physical_qubits(mapper1: QGymMapper, circuit2: Circuit) -> None:
    with pytest.raises(ValueError, match=r"QGym requires equal logical and physical qubits: logical=7, physical=5"):
        circuit2.map(mapper1)
