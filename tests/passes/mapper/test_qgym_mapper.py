import importlib.util
from collections.abc import Generator
from typing import Any

import networkx as nx
import numpy as np
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


@pytest.fixture(autouse=True)
def reset_torch_cache() -> Generator[None, None, None]:
    """Reset PyTorch's artifact registry."""
    yield
    try:
        from torch.compiler._cache import CacheArtifactFactory

        if hasattr(CacheArtifactFactory, "_artifact_types"):
            CacheArtifactFactory._artifact_types.clear()
    except (ImportError, AttributeError):
        pass


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
    mapping = mapper.map(circuit, circuit.qubit_register_size)

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
    msg = (
        "number of logical qubits 7 is not equal to the number of physical qubits 5: the QGym mapper requires them to"
        " be equal"
    )
    with pytest.raises(ValueError, match=msg):
        circuit2.map(mapper1)


def test_circuit_interaction_graph_property(circuit1: Circuit) -> None:
    graph = circuit1.interaction_graph

    assert (0, 1) in graph
    assert (1, 2) in graph
    assert (2, 4) in graph
    assert (3, 4) in graph

    assert all(weight == 1 for weight in graph.values())


def test_qgym_mapper_uses_provided_interaction_graph(
    monkeypatch: pytest.MonkeyPatch, mapper1: QGymMapper, circuit1: Circuit
) -> None:
    """Verify QGymMapper uses interaction_graph parameter if provided."""
    used_interaction_graph = {"called": False}
    used_ir = {"called": False}

    def mock_convert_interaction_graph(_: Any) -> Any:
        used_interaction_graph["called"] = True
        return nx.Graph()

    def mock_ir_to_graph(_: Any) -> Any:
        used_ir["called"] = True
        return nx.Graph()

    monkeypatch.setattr(mapper1, "_convert_interaction_graph", mock_convert_interaction_graph)
    monkeypatch.setattr(mapper1, "_ir_to_graph", mock_ir_to_graph)

    obs = np.asarray(mapper1.env.observation_space.sample())
    identity_mapping = np.arange(circuit1.qubit_register_size)
    final_obs = {"mapping": identity_mapping}

    def fake_reset(*, options: Any) -> Any:
        return obs, {}

    def fake_predict(_obs: Any, deterministic: bool = True) -> Any:
        return 0, None

    def fake_step(_action: Any) -> Any:
        return final_obs, 0.0, True, False, {}

    monkeypatch.setattr(mapper1.env, "reset", fake_reset)
    monkeypatch.setattr(mapper1.env, "step", fake_step)
    monkeypatch.setattr(mapper1.agent, "predict", fake_predict)

    mapper1.map(circuit1, circuit1.qubit_register_size)

    assert used_interaction_graph["called"] is True
    assert used_ir["called"] is False


def test_qgym_mapper_falls_back_to_ir_graph(monkeypatch: pytest.MonkeyPatch, mapper1: QGymMapper) -> None:
    """Verify QGymMapper computes graph from IR when interaction_graph is empty."""
    # Since the interaction graph is now a property of the circuit, it technically cannot be None.
    # Thus, create a circuit with only single-qubit gates, so that the interaction graph is empty.
    builder = CircuitBuilder(5)
    builder.H(0)
    builder.X(1)
    builder.Y(2)
    builder.Z(3)
    builder.H(4)
    circuit_no_interactions = builder.to_circuit()

    used_interaction_graph = {"called": False}
    used_ir = {"called": False}

    def mock_convert_interaction_graph(_: Any) -> Any:
        used_interaction_graph["called"] = True
        return nx.Graph()

    def mock_ir_to_graph(_: Any) -> Any:
        used_ir["called"] = True
        return nx.Graph()

    monkeypatch.setattr(mapper1, "_convert_interaction_graph", mock_convert_interaction_graph)
    monkeypatch.setattr(mapper1, "_ir_to_graph", mock_ir_to_graph)

    obs = np.asarray(mapper1.env.observation_space.sample())
    identity_mapping = np.arange(circuit_no_interactions.qubit_register_size)
    final_obs = {"mapping": identity_mapping}

    def fake_reset(*, options: Any) -> Any:
        return obs, {}

    def fake_predict(_obs: Any, deterministic: bool = True) -> Any:
        return 0, None

    def fake_step(_action: Any) -> Any:
        return final_obs, 0.0, True, False, {}

    monkeypatch.setattr(mapper1.env, "reset", fake_reset)
    monkeypatch.setattr(mapper1.env, "step", fake_step)
    monkeypatch.setattr(mapper1.agent, "predict", fake_predict)

    mapper1.map(circuit_no_interactions, circuit_no_interactions.qubit_register_size)

    assert used_interaction_graph["called"] is False
    assert used_ir["called"] is True
