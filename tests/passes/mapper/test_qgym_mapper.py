import importlib.util

import pytest

from opensquirrel import CircuitBuilder
from opensquirrel.circuit import Circuit
from opensquirrel.passes.mapper import QGymMapper
from opensquirrel.passes.mapper.mapping import Mapping
from tests import PROJECT_ROOT_PATH, STATIC_DATA

if importlib.util.find_spec("qgym") is None:
    pytest.skip("qgym not installed; skipping QGym mapper tests", allow_module_level=True)

if importlib.util.find_spec("stable_baselines3") is None and importlib.util.find_spec("sb3_contrib") is None:
    pytest.skip("stable-baselines3 and sb3_contrib not installed; skipping QGym mapper tests", allow_module_level=True)

QGYM_MAPPER_DATA_PATH = PROJECT_ROOT_PATH / "data" / "qgym_mapper"
AGENT_CLASS = "TRPO"


@pytest.fixture
def mapper1() -> QGymMapper:
    agent_class = AGENT_CLASS
    agent_path = str(QGYM_MAPPER_DATA_PATH / "TRPO_tuna5_2e5.zip")
    connectivity = STATIC_DATA["backends"]["tuna-5"]["connectivity"]
    return QGymMapper(agent_class, agent_path, connectivity)


@pytest.fixture
def mapper2() -> QGymMapper:
    agent_class = AGENT_CLASS
    agent_path = str(QGYM_MAPPER_DATA_PATH / "TRPO_starmon7_5e5.zip")
    connectivity = STATIC_DATA["backends"]["starmon-7"]["connectivity"]
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
        r"The QGym mapper requires an equal number of logical and physical qubits."
        r"Respectively, got 7 logical and 5 physical qubits instead."
    )
    with pytest.raises(ValueError, match=expected_error):
        circuit2.map(mapper1)
