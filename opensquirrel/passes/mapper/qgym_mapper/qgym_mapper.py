from __future__ import annotations

import importlib
from itertools import combinations
from typing import TYPE_CHECKING, Any, cast

import networkx as nx
from qgym.envs import InitialMapping

from opensquirrel.ir import IR, Instruction
from opensquirrel.passes.mapper.general_mapper import Mapper
from opensquirrel.passes.mapper.mapping import Mapping

if TYPE_CHECKING:
    from stable_baselines3.common.base_class import BaseAlgorithm


class QGymMapper(Mapper):
    """QGym-based mapper pass using a Stable-Baselines3 agent."""

    def __init__(
        self,
        agent_class: str,
        agent_path: str,
        hardware_connectivity: dict[str, list[int]],
        env_kwargs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.hardware_connectivity = self._build_connectivity_graph(hardware_connectivity)
        self.env = InitialMapping(connection_graph=self.hardware_connectivity, **(env_kwargs or {}))
        self.agent = self._load_agent(agent_class, agent_path)

    def _build_connectivity_graph(self, connectivity: dict[str, list[int]]) -> nx.Graph:
        """Convert connectivity dictionary to NetworkX graph.

        Args:
            connectivity: Dictionary with connectivity scheme (e.g., {"edges": [[0,1], [1,2]]}).

        Returns:
            NetworkX graph representing the hardware connectivity.
        """
        graph = nx.Graph()
        if isinstance(connectivity, dict):
            edges = connectivity.get("edges", next(iter(connectivity.values())) if connectivity else [])
        else:
            edges = connectivity
        graph.add_edges_from(edges)
        return graph

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
            msg = (
                f"The QGym mapper requires an equal number of logical and physical  qubits.  "
                f"Respectively, got {qubit_register_size} logical and {num_physical} physical qubits instead."
            )
            raise ValueError(msg)

        circuit_graph = self._ir_to_interaction_graph(ir)

        obs, _ = self.env.reset(options={"interaction_graph": circuit_graph})

        done = False
        last_obs: Any = obs
        while not done:
            action, _ = self.agent.predict(obs, deterministic=True)
            obs, _, terminated, truncated, _ = self.env.step(action)
            done = terminated or truncated
            last_obs = obs

        return self._get_mapping(last_obs, qubit_register_size)

    def _ir_to_interaction_graph(self, ir: IR) -> nx.Graph:
        """Build an undirected interaction graph representation of the IR.

        Args:
            ir: Intermediate representation of the quantum circuit.

        Returns:
            NetworkX graph representation of the quantum circuit, compatible with QGym.
        """
        interaction_graph = nx.Graph()
        for statement in ir.statements:
            if not isinstance(statement, Instruction):
                continue
            instruction = cast("Instruction", statement)  # type: ignore[redundant-cast]
            qubit_indices = [q.index for q in instruction.get_qubit_operands()]
            for q_index in qubit_indices:
                interaction_graph.add_node(q_index)
            if len(qubit_indices) >= 2:
                for q_i, q_j in combinations(qubit_indices, 2):
                    if interaction_graph.has_edge(q_i, q_j):
                        interaction_graph[q_i][q_j]["weight"] = interaction_graph[q_i][q_j].get("weight", 1) + 1
                    else:
                        interaction_graph.add_edge(q_i, q_j, weight=1)
        return interaction_graph

    def _get_mapping(self, last_obs: Any, qubit_register_size: int) -> Mapping:
        """Extract and convert QGym's physical-to-logical mapping to OpenSquirrel's logical-to-physical mapping.

        Args:
            last_obs: Final observation from the QGym environment containing the mapping.
            qubit_register_size: Number of qubits.

        Returns:
            Mapping object where index=logical qubit, value=physical qubit.

        Raises:
            RuntimeError: If 'mapping' key is not found in the observation.
            ValueError: If mapping length doesn't match qubit_register_size.
            ValueError: If the mapping is incomplete (not all logical qubits are mapped).
        """
        if not isinstance(last_obs, dict) or last_obs.get("mapping") is None:
            msg = "QGym environment did not provide 'mapping' in observation."
            raise RuntimeError(msg)

        mapping_data = last_obs["mapping"]
        physical_to_logical = mapping_data.tolist()

        if len(physical_to_logical) != qubit_register_size:
            msg = (
                f"Mapping length {len(physical_to_logical)} is not equal to "
                f"the size of the qubit register {qubit_register_size}."
            )
            raise ValueError(msg)

        logical_to_physical = [-1] * qubit_register_size
        for physical_qubit, logical_qubit in enumerate(physical_to_logical):
            if logical_qubit < qubit_register_size:
                logical_to_physical[logical_qubit] = physical_qubit

        if -1 in logical_to_physical:
            msg = f"Incomplete mapping. Physical-to-logical: {physical_to_logical}"
            raise ValueError(msg)

        return Mapping(logical_to_physical)
