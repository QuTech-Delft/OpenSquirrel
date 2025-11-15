from __future__ import annotations

import importlib
from itertools import combinations
from typing import TYPE_CHECKING, Any

import networkx as nx
from qgym.envs import InitialMapping

from opensquirrel.ir import IR, Instruction
from opensquirrel.passes.mapper.general_mapper import Mapper
from opensquirrel.passes.mapper.mapping import Mapping

if TYPE_CHECKING:
    from stable_baselines3.common.base_class import BaseAlgorithm


class QGymMapper(Mapper):
    """
    QGym-based Mapper using a Stable-Baselines3 agent.
    - Builds a qubit interaction graph from the IR.
    - Runs the InitialMapping environment with the trained agent.
    - Returns a Mapping compatible with OpenSquirrel.
    """

    def __init__(
        self,
        agent_class: str,
        agent_path: str,
        hardware_connectivity: nx.Graph,
        env_kwargs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.env = InitialMapping(connection_graph=hardware_connectivity, **(env_kwargs or {}))
        self.hardware_connectivity = hardware_connectivity
        self.agent = self._load_agent(agent_class, agent_path)

    def _load_agent(self, agent_class: str, agent_path: str) -> BaseAlgorithm:
        """Load a trained Stable-Baselines3 agent from a file."""
        if agent_class in ["PPO", "A2C"]:
            sb3 = importlib.import_module("stable_baselines3")
        else:
            sb3 = importlib.import_module("sb3_contrib")
        agent_cls = getattr(sb3, agent_class)
        return agent_cls.load(agent_path)

    def map(self, ir: IR, qubit_register_size: int) -> Mapping:
        """
        Compute an initial logical-to-physical qubit mapping using a trained
        Stable-Baselines3 agent acting in the QGym InitialMapping environment.

        Args:
            ir (IR): Intermediate representation of the quantum circuit to be mapped.
            qubit_register_size (int): Number of logical (virtual) qubits in the circuit.

        Returns:
            Mapping: Mapping from virtual to physical qubits.

        Raises:
            ValueError: If the number of logical qubits differs from the number of physical qubits.
            ValueError: If the agent produces an incomplete or invalid mapping.
            RuntimeError: If no 'mapping' key is found in the final observation.
        """
        num_physical = self.hardware_connectivity.number_of_nodes()
        if qubit_register_size != num_physical:
            error_msg = f"QGym requires equal logical and physical qubits: logical={qubit_register_size}, physical={num_physical}"  # noqa: E501
            raise ValueError(error_msg)

        circuit_graph = self._ir_to_interaction_graph(ir)

        obs, _ = self.env.reset(options={"interaction_graph": circuit_graph})

        done = False
        last_obs: Any = obs
        while not done:
            action, _ = self.agent.predict(obs, deterministic=True)
            obs, _, terminated, truncated, _ = self.env.step(action)
            done = terminated or truncated
            last_obs = obs

        mapping_data = self._extract_mapping_data(last_obs)
        return self._get_mapping(mapping_data, qubit_register_size)

    def _ir_to_interaction_graph(self, ir: IR) -> nx.Graph:
        """Build an undirected interaction graph representation of the IR."""
        interaction_graph = nx.Graph()
        for instr in ir.statements:
            if not isinstance(instr, Instruction):
                continue
            qubit_indices = [q.index for q in instr.get_qubit_operands()]
            for q_index in qubit_indices:
                interaction_graph.add_node(q_index)
            if len(qubit_indices) >= 2:
                for q_i, q_j in combinations(qubit_indices, 2):
                    if interaction_graph.has_edge(q_i, q_j):
                        interaction_graph[q_i][q_j]["weight"] = interaction_graph[q_i][q_j].get("weight", 1) + 1
                    else:
                        interaction_graph.add_edge(q_i, q_j, weight=1)
        return interaction_graph

    def _get_mapping(self, mapping_data: Any, qubit_register_size: int) -> Mapping:
        """Convert QGym's physical-to-logical mapping to OpenSquirrel's logical-to-physical mapping."""
        physical_to_logical = mapping_data.tolist()

        if len(physical_to_logical) != qubit_register_size:
            error_msg = f"Mapping length {len(physical_to_logical)} != qubit_register_size {qubit_register_size}."
            raise ValueError(error_msg)

        logical_to_physical = [-1] * qubit_register_size
        for physical_qubit, logical_qubit in enumerate(physical_to_logical):
            if logical_qubit < qubit_register_size:
                logical_to_physical[logical_qubit] = physical_qubit

        if -1 in logical_to_physical:
            error_msg = f"Incomplete mapping. Physical-to-logical: {physical_to_logical}"
            raise ValueError(error_msg)

        return Mapping(logical_to_physical)

    def _extract_mapping_data(self, last_obs: Any) -> Any:
        """Extract mapping from the observation dict only."""
        if isinstance(last_obs, dict) and last_obs.get("mapping") is not None:
            return last_obs["mapping"]
        error_msg = "QGym env did not provide 'mapping' in observation."
        raise RuntimeError(error_msg)
