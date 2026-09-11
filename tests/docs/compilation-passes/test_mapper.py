import importlib.util
from collections.abc import Generator

import pytest

from opensquirrel import CircuitBuilder
from opensquirrel.passes.mapper import MIPMapper, QGymMapper

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


class TestQGymMapper:
    def test_qgym_mapper(self) -> None:
        agent_path = "data/qgym_mapper/TRPO_tuna5_2e5.zip"

        connectivity = {
            "0": [2],
            "1": [2],
            "2": [0, 1, 3, 4],
            "3": [2],
            "4": [2],
        }

        qgym_mapper = QGymMapper(agent_class="TRPO", agent_path=agent_path, connectivity=connectivity)

        builder = CircuitBuilder(5)
        builder.H(0)
        builder.CNOT(0, 1)
        builder.H(2)
        builder.CNOT(1, 2)
        builder.CNOT(2, 4)
        builder.CNOT(3, 4)
        circuit = builder.to_circuit()

        initial_circuit_str = str(circuit)

        circuit.map(mapper=qgym_mapper)

        assert str(circuit) != initial_circuit_str


class TestMIPMapper:
    @pytest.fixture
    def connectivity(self) -> dict[str, list[int]]:
        return {"0": [1], "1": [0, 2], "2": [1]}

    def test_remap_to_middle_qubit(self, connectivity: dict[str, list[int]]) -> None:
        builder = CircuitBuilder(3)
        builder.H(0)
        builder.CNOT(0, 1)
        builder.CNOT(0, 2)
        circuit = builder.to_circuit()

        circuit.map(mapper=MIPMapper(connectivity=connectivity))

        assert (
            str(circuit)
            == """version 3.0

qubit[3] q

H q[1]
CNOT q[1], q[0]
CNOT q[1], q[2]
"""
        )

    def test_identity_mapping(self, connectivity: dict[str, list[int]]) -> None:
        builder = CircuitBuilder(3)
        builder.H(0)
        builder.CNOT(0, 1)
        builder.CNOT(1, 2)
        circuit = builder.to_circuit()

        circuit.map(mapper=MIPMapper(connectivity=connectivity))

        assert (
            str(circuit)
            == """version 3.0

qubit[3] q

H q[0]
CNOT q[0], q[1]
CNOT q[1], q[2]
"""
        )

    def test_remap_measurements(self, connectivity: dict[str, list[int]]) -> None:
        builder = CircuitBuilder(3, 3)
        builder.H(0)
        builder.CNOT(0, 1)
        builder.CNOT(0, 2)
        builder.measure(0, 0)
        builder.measure(1, 1)
        builder.measure(2, 2)
        circuit = builder.to_circuit()

        circuit.map(mapper=MIPMapper(connectivity=connectivity))

        assert (
            str(circuit)
            == """version 3.0

qubit[3] q
bit[3] b

H q[1]
CNOT q[1], q[0]
CNOT q[1], q[2]
b[0] = measure q[1]
b[1] = measure q[0]
b[2] = measure q[2]
"""
        )

    def test_timeout(self, connectivity: dict[str, list[int]]) -> None:
        builder = CircuitBuilder(3)
        builder.H(0)
        builder.CNOT(0, 1)
        builder.CNOT(0, 2)
        circuit = builder.to_circuit()

        mip_mapper = MIPMapper(connectivity=connectivity, timeout=0.000001)

        with pytest.raises(RuntimeError, match="MIP solver failed to find a feasible mapping"):
            circuit.map(mapper=mip_mapper)
