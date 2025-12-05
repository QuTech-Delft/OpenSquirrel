# Tests for the QGymMapper class
import importlib.util
import json
from importlib.resources import files

import pytest

from opensquirrel import CircuitBuilder
from opensquirrel.circuit import Circuit
from opensquirrel.passes.mapper import QGymMapper
from opensquirrel.passes.mapper.mapping import Mapping

if importlib.util.find_spec("qgym") is None:
    pytest.skip("qgym not installed; skipping QGym mapper tests", allow_module_level=True)

if importlib.util.find_spec("stable_baselines3") is None and importlib.util.find_spec("sb3_contrib") is None:
    pytest.skip("stable-baselines3 and sb3_contrib not installed; skipping QGym mapper tests", allow_module_level=True)

CONNECTIVITY_SCHEMES = json.loads(
    (files("opensquirrel.passes.mapper.qgym_mapper") / "connectivities.json").read_text(encoding="utf-8")
)
PATH_TO_AGENT1 = "opensquirrel/passes/mapper/qgym_mapper/TRPO_tuna5_2e5.zip"
PATH_TO_AGENT2 = "opensquirrel/passes/mapper/qgym_mapper/TRPO_starmon7_5e5.zip"
AGENT_CLASS = "TRPO"


@pytest.fixture
def mapper1() -> QGymMapper:
    agent_class = AGENT_CLASS
    agent_path = PATH_TO_AGENT1
    connectivity = CONNECTIVITY_SCHEMES["tuna-5"]
    return QGymMapper(agent_class, agent_path, connectivity)


@pytest.fixture
def mapper2() -> QGymMapper:
    agent_class = AGENT_CLASS
    agent_path = PATH_TO_AGENT2
    connectivity = CONNECTIVITY_SCHEMES["starmon-7"]
    return QGymMapper(agent_class, agent_path, connectivity)


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
    ids=["tuna-5-mapping", "starmon-7-mapping"],
)
def test_mapping(
    mapper: QGymMapper, circuit: Circuit, expected_mapping_length: int, request: pytest.FixtureRequest
) -> None:
    circuit = request.getfixturevalue(circuit)  # type: ignore[arg-type]
    mapper = request.getfixturevalue(mapper)  # type: ignore[arg-type]
    mapping = mapper.map(circuit.ir, circuit.qubit_register_size)

    assert isinstance(mapping, Mapping)
    assert len(mapping) == expected_mapping_length

    physical_qubits = [mapping[i] for i in range(len(mapping))]
    assert all(0 <= physical_qubit < expected_mapping_length for physical_qubit in physical_qubits)

    assert len(set(physical_qubits)) == expected_mapping_length, "Mapping contains duplicate physical qubits"


def test_map_on_circuit(mapper1: QGymMapper, circuit1: Circuit) -> None:
    initial_circuit = str(circuit1)
    circuit1.map(mapper=mapper1)
    assert str(circuit1) != initial_circuit


def test_unequal_number_logical_and_physical_qubits(mapper1: QGymMapper, circuit2: Circuit) -> None:
    expected_error = (
        r"The QGym mapper requires an equal number of logical and physical  qubits.  "
        r"Respectively, got 7 logical and 5 physical qubits instead."
    )
    with pytest.raises(ValueError, match=expected_error):
        circuit2.map(mapper1)
