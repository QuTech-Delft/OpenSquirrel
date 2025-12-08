import importlib.util
import json
from importlib.resources import files

import pytest

from opensquirrel import CircuitBuilder
from opensquirrel.passes.mapper import QGymMapper

if importlib.util.find_spec("qgym") is None:
    pytest.skip("qgym not installed; skipping QGym mapper tests", allow_module_level=True)

if importlib.util.find_spec("stable_baselines3") is None and importlib.util.find_spec("sb3_contrib") is None:
    pytest.skip("stable-baselines3 and sb3_contrib not installed; skipping QGym mapper tests", allow_module_level=True)


class TestQGymMapper:
    def test_qgym_mapper(self) -> None:
        agent_path = "opensquirrel/passes/mapper/qgym_mapper/TRPO_tuna5_2e5.zip"

        connectivity_schemes = json.loads(
            (files("opensquirrel.passes.mapper.qgym_mapper") / "connectivities.json").read_text(encoding="utf-8")
        )

        connectivity = connectivity_schemes["tuna-5"]

        builder = CircuitBuilder(5)
        builder.H(0)
        builder.CNOT(0, 1)
        builder.H(2)
        builder.CNOT(1, 2)
        builder.CNOT(2, 4)
        builder.CNOT(3, 4)
        circuit = builder.to_circuit()

        agent_class = "TRPO"
        qgym_mapper = QGymMapper(agent_class=agent_class, agent_path=agent_path, hardware_connectivity=connectivity)

        initial_circuit_str = str(circuit)

        circuit.map(mapper=qgym_mapper)

        assert str(circuit) != initial_circuit_str
