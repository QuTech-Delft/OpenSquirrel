from __future__ import annotations

import importlib
from itertools import combinations
from typing import TYPE_CHECKING, Any, cast

import networkx as nx

from opensquirrel.ir import IR, Instruction
from opensquirrel.passes.mapper.general_mapper import Mapper
from opensquirrel.passes.mapper.mapping import Mapping

try:
    from qgym.envs import InitialMapping
except ModuleNotFoundError:
    pass

if TYPE_CHECKING:
    from opensquirrel import Circuit, Connectivity

    try:
        from stable_baselines3.common.base_class import BaseAlgorithm
    except ModuleNotFoundError:
        pass


class QGymMapper(Mapper):
    """QGym-based mapper pass using a Stable-Baselines3 agent."""

    def __init__(
        self,
        agent_class: str,
        agent_path: str,
        connectivity: Connectivity,
        env_kwargs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.hardware_connectivity = self._build_connectivity_graph(connectivity)
        self.env = InitialMapping(connection_graph=self.hardware_connectivity, **(env_kwargs or {}))
        self.agent = self._load_agent(agent_class, agent_path)

    def map(
        self,
        circuit: Circuit,
        qubit_register_size: int,
    ) -> Mapping:
        """
        Compute an initial logical-to-physical qubit mapping using a trained Stable-Baselines3
        agent acting in the QGym InitialMapping environment.

        Args:
            circuit (Circuit): The quantum circuit to be mapped.
            qubit_register_size (int): Number of logical (virtual) qubits in the circuit.

        Returns:
            Mapping from virtual to physical qubits.

        Raises:
            ValueError: If the number of logical qubits differs from the number of physical qubits.
            ValueError: If the agent produces an incomplete or invalid mapping.
            RuntimeError: If no mapping key is found in the final observation.

        """
        num_physical = self.hardware_connectivity.number_of_nodes()
        if qubit_register_size != num_physical:
            msg = (
                f"number of logical qubits {qubit_register_size!r} is not equal to the number of physical qubits"
                f" {num_physical!r}: the QGym mapper requires them to be equal"
            )
            raise ValueError(msg)

        circuit_graph = (
            self._ir_to_graph(circuit.ir)
            if not circuit.interaction_graph
            else self._convert_interaction_graph(circuit.interaction_graph)
        )

        obs, _ = self.env.reset(options={"interaction_graph": circuit_graph})

        done = False
        last_obs: Any = obs
        while not done:
            action, _ = self.agent.predict(obs, deterministic=True)
            obs, _, terminated, truncated, _ = self.env.step(action)
            done = terminated or truncated
            last_obs = obs

        return self._get_mapping(last_obs, qubit_register_size)

    @staticmethod
    def _build_connectivity_graph(connectivity: Connectivity) -> nx.Graph:
        """Convert connectivity dictionary to NetworkX graph.

        Args:
            connectivity (Connectivity): Connectivity of the target backend.

        Returns:
            NetworkX graph representing the hardware connectivity.
        """
        edges = []
        for qubit_start, qubit_ends in connectivity.items():
            for qubit_end in qubit_ends:
                if [qubit_end, int(qubit_start)] in edges:
                    continue
                edges.append([int(qubit_start), qubit_end])
        graph = nx.Graph()
        graph.add_edges_from(edges)
        return graph

    @staticmethod
    def _load_agent(agent_class: str, agent_path: str) -> BaseAlgorithm:
        """Load a trained Stable-Baselines3 agent from a file."""
        if agent_class in ["PPO", "A2C"]:
            sb3 = importlib.import_module("stable_baselines3")
        else:
            sb3 = importlib.import_module("sb3_contrib")
        agent_cls = getattr(sb3, agent_class)
        return cast("BaseAlgorithm", agent_cls.load(agent_path))

    @staticmethod
    def _ir_to_graph(ir: IR) -> nx.Graph:
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
            qubit_indices = statement.qubit_indices
            for q_index in qubit_indices:
                interaction_graph.add_node(q_index)
            if len(qubit_indices) >= 2:
                for q_i, q_j in combinations(qubit_indices, 2):
                    if interaction_graph.has_edge(q_i, q_j):
                        interaction_graph[q_i][q_j]["weight"] = interaction_graph[q_i][q_j].get("weight", 1) + 1
                    else:
                        interaction_graph.add_edge(q_i, q_j, weight=1)
        return interaction_graph

    @staticmethod
    def _convert_interaction_graph(edges: dict[tuple[int, int], int]) -> nx.Graph:
        """Convert Circuit's simple interaction graph to NetworkX graph.

        Args:
            edges: Dictionary mapping (qubit_i, qubit_j) tuples to interaction weights.

        Returns:
            NetworkX graph representation of the quantum circuit, compatible with QGym.
        """
        graph = nx.Graph()

        all_nodes = set()
        for q_i, q_j in edges:
            all_nodes.add(q_i)
            all_nodes.add(q_j)
        graph.add_nodes_from(all_nodes)

        for (q_i, q_j), weight in edges.items():
            graph.add_edge(q_i, q_j, weight=weight)

        return graph

    @staticmethod
    def _get_mapping(last_obs: Any, qubit_register_size: int) -> Mapping:
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
            msg = "QGym environment did not provide 'mapping' in observation"
            raise RuntimeError(msg)

        mapping_data = last_obs["mapping"]
        physical_to_logical = mapping_data.tolist()

        if len(physical_to_logical) != qubit_register_size:
            msg = (
                f"the size of the mapping {len(physical_to_logical)!r} is not equal to "
                f"the number of qubits {qubit_register_size!r}."
            )
            raise ValueError(msg)

        logical_to_physical = [-1] * qubit_register_size
        for physical_qubit, logical_qubit in enumerate(physical_to_logical):
            if logical_qubit < qubit_register_size:
                logical_to_physical[logical_qubit] = physical_qubit

        if -1 in logical_to_physical:
            msg = f"mapping is incomplete: obtained mapping {physical_to_logical!r}"
            raise ValueError(msg)

        return Mapping(logical_to_physical)
